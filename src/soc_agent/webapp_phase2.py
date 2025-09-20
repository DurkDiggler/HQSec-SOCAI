"""SOC Agent WebApp Phase 2 - Enhanced with Database and Caching"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import json
import logging
import redis
import asyncio
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./soc_agent.db"  # Using SQLite for Phase 2 simplicity
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup (with fallback)
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()  # Test connection
    redis_available = True
except:
    redis_client = None
    redis_available = False

# Database Models
class SecurityEvent(Base):
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    severity = Column(String, index=True)
    source_ip = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, index=True)
    alert_type = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)

# Pydantic models
class SecurityEventCreate(BaseModel):
    event_type: str
    severity: str
    source_ip: Optional[str] = None
    message: str

class AlertResponse(BaseModel):
    id: int
    event_id: int
    alert_type: str
    message: str
    timestamp: datetime
    acknowledged: bool

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Create FastAPI app
app = FastAPI(
    title="SOC Agent - Phase 2",
    description="Security Operations Center Agent - Enhanced with Database and Real-time Features",
    version="2.0.0"
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
    return {"message": "SOC Agent - Phase 2", "status": "running", "features": ["database", "caching", "realtime"]}

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    # Check database connection
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Redis connection
    if redis_available:
        try:
            redis_client.ping()
            redis_status = "healthy"
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
    else:
        redis_status = "not available"
    
    return {
        "status": "healthy",
        "service": "soc-agent-phase2",
        "database": db_status,
        "redis": redis_status
    }

@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "status": "operational",
        "version": "2.0.0",
        "features": ["database", "caching", "realtime", "alerts", "ml-basic"]
    }

@app.post("/api/v1/webhook")
async def webhook_endpoint(event_data: SecurityEventCreate, db: Session = Depends(get_db)):
    """Enhanced webhook endpoint with database storage"""
    logger.info(f"Received webhook data: {event_data}")
    
    # Create security event
    db_event = SecurityEvent(
        event_type=event_data.event_type,
        severity=event_data.severity,
        source_ip=event_data.source_ip,
        message=event_data.message,
        risk_score=calculate_risk_score(event_data)
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Create alert if high severity
    if event_data.severity in ["high", "critical"]:
        alert = Alert(
            event_id=db_event.id,
            alert_type="security_alert",
            message=f"High severity event: {event_data.message}"
        )
        db.add(alert)
        db.commit()
        
        # Broadcast real-time alert
        await manager.broadcast(json.dumps({
            "type": "alert",
            "data": {
                "id": alert.id,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat()
            }
        }))
    
    # Cache the event (if Redis is available)
    if redis_available:
        try:
            redis_client.setex(f"event:{db_event.id}", 3600, json.dumps({
                "id": db_event.id,
                "event_type": db_event.event_type,
                "severity": db_event.severity,
                "timestamp": db_event.timestamp.isoformat()
            }))
        except Exception as e:
            logger.warning(f"Failed to cache event: {e}")
    
    return {"status": "received", "event_id": db_event.id, "risk_score": db_event.risk_score}

@app.get("/api/v1/events")
async def get_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get security events"""
    events = db.query(SecurityEvent).offset(skip).limit(limit).all()
    return {"events": events, "count": len(events)}

@app.get("/api/v1/alerts")
async def get_alerts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get alerts"""
    alerts = db.query(Alert).offset(skip).limit(limit).all()
    return {"alerts": alerts, "count": len(alerts)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def calculate_risk_score(event: SecurityEventCreate) -> float:
    """Simple risk scoring algorithm"""
    base_score = 0.0
    
    # Severity scoring
    severity_scores = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
    base_score += severity_scores.get(event.severity, 0.0)
    
    # Event type scoring
    if event.event_type in ["malware", "intrusion", "data_breach"]:
        base_score += 0.3
    
    return min(base_score, 1.0)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
