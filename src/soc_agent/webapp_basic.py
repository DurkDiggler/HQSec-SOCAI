"""Basic SOC Agent WebApp - Minimal working version"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SOC Agent - Basic Version",
    description="Security Operations Center Agent - Minimal Working Version",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "SOC Agent - Basic Version", "status": "running"}

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "soc-agent-basic"}

@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "status": "operational",
        "version": "1.0.0",
        "features": ["basic-api", "health-check"]
    }

@app.post("/api/v1/webhook")
async def webhook_endpoint(data: dict):
    """Basic webhook endpoint"""
    logger.info(f"Received webhook data: {data}")
    return {"status": "received", "message": "Webhook processed successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
