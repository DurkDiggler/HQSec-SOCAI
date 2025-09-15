from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from importlib import metadata

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

from .adapters import normalize_event
from .analyzer import enrich_and_score
from .api import api_router
from .autotask import create_autotask_ticket
from .config import SETTINGS
from .database import create_tables, get_db, save_alert
from .logging import setup_json_logging
from .models import EventIn
from .notifiers import send_email
from .security import WebhookAuth

try:
    VERSION = metadata.version("soc_agent")
except metadata.PackageNotFoundError:  # pragma: no cover - fallback for non-installed package
    VERSION = "0.0.0"

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
rate_limit_storage: defaultdict[str, list] = defaultdict(list)

app = FastAPI(
    title="SOC Agent – Webhook Analyzer", 
    version=VERSION,
    description="Security Operations Center webhook analyzer with threat intelligence enrichment",
    docs_url="/docs" if SETTINGS.log_level == "DEBUG" else None,
    redoc_url="/redoc" if SETTINGS.log_level == "DEBUG" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Setup logging
setup_json_logging()

# Create database tables
create_tables()

# Include API router
app.include_router(api_router)


def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit."""
    current_time = time.time()
    window_start = current_time - SETTINGS.rate_limit_window
    
    # Clean old entries
    rate_limit_storage[client_ip] = [
        timestamp for timestamp in rate_limit_storage[client_ip] 
        if timestamp > window_start
    ]
    
    # Check if under limit
    if len(rate_limit_storage[client_ip]) >= SETTINGS.rate_limit_requests:
        return False
    
    # Add current request
    rate_limit_storage[client_ip].append(current_time)
    return True


@app.get("/")
def root():
    """Root endpoint with service information."""
    return {
        "ok": True, 
        "service": "SOC Agent – Webhook Analyzer", 
        "version": VERSION,
        "status": "operational"
    }


@app.get("/healthz")
def healthz():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": time.time()}


@app.get("/readyz")
def readyz():
    """Readiness check endpoint."""
    # Check external dependencies
    checks = {
        "database": True,  # Add actual DB check if needed
        "external_apis": True,  # Add actual API checks if needed
    }
    
    all_ready = all(checks.values())
    status_code = status.HTTP_200_OK if all_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        content={"status": "ready" if all_ready else "not ready", "checks": checks},
        status_code=status_code
    )


@app.get("/metrics")
def metrics():
    """Basic metrics endpoint."""
    if not SETTINGS.enable_metrics:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    
    return {
        "requests_total": sum(len(requests) for requests in rate_limit_storage.values()),
        "active_clients": len(rate_limit_storage),
        "cache_size": len(getattr(intel_client, '_cache', {})),
    }


@app.post("/webhook")
async def webhook(req: Request):
    """Main webhook endpoint for processing security events."""
    # Get client IP for rate limiting
    client_ip = req.client.host if req.client else "unknown"
    
    # Check rate limit
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for client: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    # Check request size
    content_length = req.headers.get("content-length")
    if content_length and int(content_length) > SETTINGS.max_request_size:
        logger.warning(f"Request too large from {client_ip}: {content_length} bytes")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Request too large"
        )
    
    try:
        body = await req.body()
    except Exception as e:
        logger.error(f"Failed to read request body from {client_ip}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read request body")

    # Optional shared-secret or HMAC verification
    if SETTINGS.webhook_shared_secret:
        provided = req.headers.get("X-Webhook-Secret")
        if not WebhookAuth.verify_shared_secret(provided, SETTINGS.webhook_shared_secret):
            logger.warning(f"Invalid webhook secret from {client_ip}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")
    
    if SETTINGS.webhook_hmac_secret:
        signature = req.headers.get(SETTINGS.webhook_hmac_header)
        if not WebhookAuth.verify_hmac(
            body, signature, SETTINGS.webhook_hmac_secret, SETTINGS.webhook_hmac_prefix
        ):
            logger.warning(f"Invalid HMAC signature from {client_ip}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid HMAC signature")

    try:
        event = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from {client_ip}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON from {client_ip}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request format")

    try:
        # Normalize vendor payloads first
        normalized = normalize_event(event)
        logger.debug(f"Normalized event from {client_ip}: {normalized.get('source', 'unknown')}")

        # Validate normalized payload
        payload = EventIn.model_validate(normalized)
        logger.info(f"Processing event from {client_ip}: {payload.event_type} (severity: {payload.severity})")

    except Exception as e:
        logger.error(f"Invalid payload from {client_ip}: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid payload: {e}")

    try:
        # Analyze and score the event
        result = enrich_and_score(payload.model_dump())
        logger.info(f"Analysis complete for {client_ip}: category={result['category']}, action={result['recommended_action']}")

    except Exception as e:
        logger.error(f"Analysis failed for {client_ip}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analysis failed")

    # Save alert to database
    try:
        db = next(get_db())
        alert = save_alert(db, payload.model_dump(), result, {})
        logger.info(f"Alert saved to database with ID: {alert.id}")
    except Exception as e:
        logger.error(f"Failed to save alert to database: {e}")
        # Continue processing even if database save fails

    # Generate notification content
    title = f"[{result['category']}] {payload.event_type or 'event'} – {payload.source or 'unknown'}"
    summary_lines = [
        f"Source: {payload.source}",
        f"Type: {payload.event_type}  Severity: {payload.severity}",
        f"Timestamp: {payload.timestamp}",
        f"Message: {payload.message}",
        f"IOCs: {json.dumps(result['iocs'])}",
        (
            f"Scores: base={result['scores']['base']} "
            f"intel={result['scores']['intel']} "
            f"final={result['scores']['final']}"
        ),
        f"Recommended action: {result['recommended_action']}",
    ]
    
    # Add intelligence details
    for ipinfo in result.get("intel", {}).get("ips", []):
        label = ",".join(ipinfo.get("labels", []))
        scr = ipinfo.get("score", 0)
        summary_lines.append(f"Intel: {ipinfo['indicator']} -> {label} (score {scr})")
    
    body_out = "\n".join(summary_lines)

    # Execute recommended actions
    actions = {}
    try:
        if result["recommended_action"] == "ticket":
            ok, msg, resp = create_autotask_ticket(title=title, description=body_out)
            actions["autotask_ticket"] = {"ok": ok, "message": msg, "response": resp}
            logger.info(f"Autotask ticket creation: {ok} - {msg}")
            
        elif result["recommended_action"] == "email":
            ok, msg = send_email(subject=title, body=body_out)
            actions["email"] = {"ok": ok, "message": msg}
            logger.info(f"Email notification: {ok} - {msg}")
            
    except Exception as e:
        logger.error(f"Action execution failed for {client_ip}: {e}")
        actions["error"] = {"message": str(e)}

    # Update alert with action results
    try:
        if 'alert' in locals():
            alert.email_sent = actions.get("email", {}).get("ok", False)
            alert.ticket_created = actions.get("autotask_ticket", {}).get("ok", False)
            if actions.get("autotask_ticket", {}).get("ok") and actions.get("autotask_ticket", {}).get("response"):
                alert.ticket_id = actions["autotask_ticket"]["response"].get("id")
            db.commit()
            logger.info(f"Alert {alert.id} updated with action results")
    except Exception as e:
        logger.error(f"Failed to update alert with action results: {e}")

    return JSONResponse({
        "analysis": result, 
        "actions": actions,
        "processed_at": time.time()
    })
