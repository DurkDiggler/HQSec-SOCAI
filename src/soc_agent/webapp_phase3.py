"""SOC Agent WebApp Phase 3 - Advanced Features with Auth, ML, and Real-time"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import json
import logging
import redis
import asyncio
import hashlib
import secrets
from typing import List, Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./soc_agent_phase3.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup (with fallback)
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    redis_available = True
except:
    redis_client = None
    redis_available = False

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

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
    ml_anomaly_score = Column(Float, default=0.0)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("security_events.id"))
    alert_type = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    event = relationship("SecurityEvent")
    acknowledged_user = relationship("User")

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

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

# Authentication
security = HTTPBearer()

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

def create_access_token(username: str) -> str:
    return secrets.token_urlsafe(32)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    user = db.query(User).filter(User.username == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

# ML Models
class ThreatDetector:
    def __init__(self):
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = "threat_detector.joblib"
        self.load_model()
    
    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                model_data = joblib.load(self.model_path)
                self.anomaly_detector = model_data['anomaly_detector']
                self.scaler = model_data['scaler']
                self.is_trained = True
                logger.info("ML model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load ML model: {e}")
    
    def save_model(self):
        try:
            model_data = {
                'anomaly_detector': self.anomaly_detector,
                'scaler': self.scaler
            }
            joblib.dump(model_data, self.model_path)
            logger.info("ML model saved successfully")
        except Exception as e:
            logger.warning(f"Failed to save ML model: {e}")
    
    def train_model(self, events_data):
        """Train the anomaly detection model"""
        try:
            # Extract features from events
            features = []
            for event in events_data:
                feature_vector = [
                    1 if event['severity'] == 'critical' else 0,
                    1 if event['severity'] == 'high' else 0,
                    1 if event['event_type'] in ['malware', 'intrusion', 'data_breach'] else 0,
                    len(event.get('message', '')),
                    event.get('risk_score', 0.0)
                ]
                features.append(feature_vector)
            
            if len(features) > 10:  # Need minimum data for training
                features = np.array(features)
                features_scaled = self.scaler.fit_transform(features)
                self.anomaly_detector.fit(features_scaled)
                self.is_trained = True
                self.save_model()
                logger.info("ML model trained successfully")
        except Exception as e:
            logger.error(f"Failed to train ML model: {e}")
    
    def detect_anomaly(self, event_data):
        """Detect if an event is anomalous"""
        if not self.is_trained:
            return 0.0
        
        try:
            feature_vector = [
                1 if event_data['severity'] == 'critical' else 0,
                1 if event_data['severity'] == 'high' else 0,
                1 if event_data['event_type'] in ['malware', 'intrusion', 'data_breach'] else 0,
                len(event_data.get('message', '')),
                event_data.get('risk_score', 0.0)
            ]
            
            features = np.array([feature_vector])
            features_scaled = self.scaler.transform(features)
            anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]
            return float(anomaly_score)
        except Exception as e:
            logger.error(f"Failed to detect anomaly: {e}")
            return 0.0

# Initialize ML model
threat_detector = ThreatDetector()

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
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Create FastAPI app
app = FastAPI(
    title="SOC Agent - Phase 3",
    description="Security Operations Center Agent - Advanced Features with Auth, ML, and Real-time",
    version="3.0.0"
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
    return {
        "message": "SOC Agent - Phase 3", 
        "status": "running", 
        "features": ["database", "caching", "realtime", "auth", "ml", "alerts"]
    }

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
        "service": "soc-agent-phase3",
        "database": db_status,
        "redis": redis_status,
        "ml_model": "trained" if threat_detector.is_trained else "untrained"
    }

# Authentication endpoints
@app.post("/api/v1/auth/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "User created successfully", "user_id": user.id}

@app.post("/api/v1/auth/login")
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is disabled")
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(user.username)
    
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

@app.post("/api/v1/webhook")
async def webhook_endpoint(event_data: SecurityEventCreate, db: Session = Depends(get_db)):
    """Enhanced webhook endpoint with ML analysis"""
    logger.info(f"Received webhook data: {event_data}")
    
    # Calculate risk score
    risk_score = calculate_risk_score(event_data)
    
    # Create security event
    db_event = SecurityEvent(
        event_type=event_data.event_type,
        severity=event_data.severity,
        source_ip=event_data.source_ip,
        message=event_data.message,
        risk_score=risk_score
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # ML anomaly detection
    event_dict = {
        'event_type': event_data.event_type,
        'severity': event_data.severity,
        'message': event_data.message,
        'risk_score': risk_score
    }
    
    anomaly_score = threat_detector.detect_anomaly(event_dict)
    db_event.ml_anomaly_score = anomaly_score
    db.commit()
    
    # Create alert if high severity or anomalous
    if event_data.severity in ["high", "critical"] or anomaly_score < -0.5:
        alert = Alert(
            event_id=db_event.id,
            alert_type="security_alert",
            message=f"High priority event: {event_data.message} (Anomaly Score: {anomaly_score:.3f})"
        )
        db.add(alert)
        db.commit()
        
        # Broadcast real-time alert
        await manager.broadcast(json.dumps({
            "type": "alert",
            "data": {
                "id": alert.id,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "anomaly_score": anomaly_score
            }
        }))
    
    # Cache the event
    if redis_available:
        try:
            redis_client.setex(f"event:{db_event.id}", 3600, json.dumps({
                "id": db_event.id,
                "event_type": db_event.event_type,
                "severity": db_event.severity,
                "timestamp": db_event.timestamp.isoformat(),
                "anomaly_score": anomaly_score
            }))
        except Exception as e:
            logger.warning(f"Failed to cache event: {e}")
    
    return {
        "status": "received", 
        "event_id": db_event.id, 
        "risk_score": risk_score,
        "anomaly_score": anomaly_score
    }

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

@app.post("/api/v1/ml/train")
async def train_ml_model(db: Session = Depends(get_db)):
    """Train the ML model with existing data"""
    events = db.query(SecurityEvent).all()
    events_data = []
    
    for event in events:
        events_data.append({
            'event_type': event.event_type,
            'severity': event.severity,
            'message': event.message,
            'risk_score': event.risk_score
        })
    
    threat_detector.train_model(events_data)
    
    return {"message": "ML model training completed", "events_used": len(events_data)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts"""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def calculate_risk_score(event: SecurityEventCreate) -> float:
    """Enhanced risk scoring algorithm"""
    base_score = 0.0
    
    # Severity scoring
    severity_scores = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
    base_score += severity_scores.get(event.severity, 0.0)
    
    # Event type scoring
    high_risk_types = ["malware", "intrusion", "data_breach", "ddos", "phishing"]
    if event.event_type in high_risk_types:
        base_score += 0.3
    
    # Source IP scoring (basic)
    if event.source_ip and event.source_ip.startswith("10."):
        base_score += 0.1  # Internal network
    
    return min(base_score, 1.0)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
