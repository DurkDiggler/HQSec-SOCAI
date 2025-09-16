"""Database models and connection management for SOC Agent."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
    desc,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .config import SETTINGS

Base = declarative_base()


class Alert(Base):
    """Alert model for storing security events."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=True, index=True)
    event_type = Column(String(100), nullable=True, index=True)
    severity = Column(Integer, default=0, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    message = Column(Text, nullable=True)
    ip = Column(String(45), nullable=True, index=True)  # IPv6 support
    username = Column(String(255), nullable=True, index=True)
    
    # Analysis results
    category = Column(String(20), nullable=True, index=True)  # LOW, MEDIUM, HIGH
    recommended_action = Column(String(20), nullable=True)  # none, email, ticket
    base_score = Column(Integer, default=0)
    intel_score = Column(Integer, default=0)
    final_score = Column(Integer, default=0)
    
    # IOC data
    iocs = Column(JSON, default=dict)
    intel_data = Column(JSON, default=dict)
    
    # Status and actions
    status = Column(String(20), default="new", index=True)  # new, acknowledged, investigating, resolved, false_positive
    assigned_to = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Actions taken
    email_sent = Column(Boolean, default=False)
    ticket_created = Column(Boolean, default=False)
    ticket_id = Column(String(100), nullable=True)
    
    # Metadata
    raw_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "event_type": self.event_type,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message": self.message,
            "ip": self.ip,
            "username": self.username,
            "category": self.category,
            "recommended_action": self.recommended_action,
            "base_score": self.base_score,
            "intel_score": self.intel_score,
            "final_score": self.final_score,
            "iocs": self.iocs,
            "intel_data": self.intel_data,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "notes": self.notes,
            "email_sent": self.email_sent,
            "ticket_created": self.ticket_created,
            "ticket_id": self.ticket_id,
            "raw_data": self.raw_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AlertStats(Base):
    """Alert statistics for dashboard."""
    
    __tablename__ = "alert_stats"
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, index=True)
    total_alerts = Column(Integer, default=0)
    high_severity = Column(Integer, default=0)
    medium_severity = Column(Integer, default=0)
    low_severity = Column(Integer, default=0)
    new_alerts = Column(Integer, default=0)
    acknowledged_alerts = Column(Integer, default=0)
    resolved_alerts = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    tickets_created = Column(Integer, default=0)


# Database setup
def get_database_url():
    """Get database URL from settings."""
    if SETTINGS.postgres_host and SETTINGS.postgres_user and SETTINGS.postgres_password and SETTINGS.postgres_db:
        return f"postgresql://{SETTINGS.postgres_user}:{SETTINGS.postgres_password}@{SETTINGS.postgres_host}:{SETTINGS.postgres_port}/{SETTINGS.postgres_db}"
    return SETTINGS.database_url

DATABASE_URL = get_database_url()

# Create engine with appropriate configuration
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_alert(
    db: Session,
    event_data: Dict[str, Any],
    analysis_result: Dict[str, Any],
    actions_taken: Dict[str, Any]
) -> Alert:
    """Save alert to database."""
    
    # Extract IOCs and intelligence data
    iocs = analysis_result.get("iocs", {})
    intel_data = analysis_result.get("intel", {})
    
    # Create alert record
    alert = Alert(
        source=event_data.get("source"),
        event_type=event_data.get("event_type"),
        severity=event_data.get("severity", 0),
        timestamp=datetime.fromisoformat(event_data.get("timestamp").replace("Z", "+00:00")) if event_data.get("timestamp") else datetime.utcnow(),
        message=event_data.get("message"),
        ip=event_data.get("ip"),
        username=event_data.get("username"),
        category=analysis_result.get("category"),
        recommended_action=analysis_result.get("recommended_action"),
        base_score=analysis_result.get("scores", {}).get("base", 0),
        intel_score=analysis_result.get("scores", {}).get("intel", 0),
        final_score=analysis_result.get("scores", {}).get("final", 0),
        iocs=iocs,
        intel_data=intel_data,
        email_sent=actions_taken.get("email", {}).get("ok", False),
        ticket_created=actions_taken.get("autotask_ticket", {}).get("ok", False),
        ticket_id=actions_taken.get("autotask_ticket", {}).get("response", {}).get("id") if actions_taken.get("autotask_ticket", {}).get("ok") else None,
        raw_data=event_data.get("raw", {}),
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return alert


def get_alerts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    severity: Optional[int] = None,
    source: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None
) -> List[Alert]:
    """Get alerts with filtering and pagination."""
    
    query = db.query(Alert)
    
    # Apply filters
    if status:
        query = query.filter(Alert.status == status)
    if severity is not None:
        query = query.filter(Alert.severity == severity)
    if source:
        query = query.filter(Alert.source == source)
    if category:
        query = query.filter(Alert.category == category)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Alert.message.ilike(search_term)) |
            (Alert.ip.ilike(search_term)) |
            (Alert.username.ilike(search_term)) |
            (Alert.event_type.ilike(search_term))
        )
    
    # Order by timestamp descending
    query = query.order_by(desc(Alert.timestamp))
    
    return query.offset(skip).limit(limit).all()


def get_alert_by_id(db: Session, alert_id: int) -> Optional[Alert]:
    """Get alert by ID."""
    return db.query(Alert).filter(Alert.id == alert_id).first()


def update_alert_status(
    db: Session,
    alert_id: int,
    status: str,
    assigned_to: Optional[str] = None,
    notes: Optional[str] = None
) -> Optional[Alert]:
    """Update alert status."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.status = status
        if assigned_to:
            alert.assigned_to = assigned_to
        if notes:
            alert.notes = notes
        alert.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
    return alert


def get_alert_statistics(db: Session, days: int = 7) -> Dict[str, Any]:
    """Get alert statistics for dashboard."""
    
    # Get date range
    from datetime import timedelta
    end_date = datetime.utcnow()
    start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)
    
    # Total alerts
    total_alerts = db.query(Alert).filter(Alert.created_at >= start_date).count()
    
    # Alerts by severity
    high_severity = db.query(Alert).filter(
        Alert.created_at >= start_date,
        Alert.severity >= 7
    ).count()
    
    medium_severity = db.query(Alert).filter(
        Alert.created_at >= start_date,
        Alert.severity >= 4,
        Alert.severity < 7
    ).count()
    
    low_severity = db.query(Alert).filter(
        Alert.created_at >= start_date,
        Alert.severity < 4
    ).count()
    
    # Alerts by status
    new_alerts = db.query(Alert).filter(
        Alert.created_at >= start_date,
        Alert.status == "new"
    ).count()
    
    acknowledged_alerts = db.query(Alert).filter(
        Alert.created_at >= start_date,
        Alert.status == "acknowledged"
    ).count()
    
    resolved_alerts = db.query(Alert).filter(
        Alert.created_at >= start_date,
        Alert.status == "resolved"
    ).count()
    
    false_positives = db.query(Alert).filter(
        Alert.created_at >= start_date,
        Alert.status == "false_positive"
    ).count()
    
    # Actions taken
    emails_sent = db.query(Alert).filter(
        Alert.created_at >= start_date,
        Alert.email_sent == True
    ).count()
    
    tickets_created = db.query(Alert).filter(
        Alert.created_at >= start_date,
        Alert.ticket_created == True
    ).count()
    
    # Recent alerts (last 24 hours)
    recent_alerts = db.query(Alert).filter(
        Alert.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    return {
        "total_alerts": total_alerts,
        "high_severity": high_severity,
        "medium_severity": medium_severity,
        "low_severity": low_severity,
        "new_alerts": new_alerts,
        "acknowledged_alerts": acknowledged_alerts,
        "resolved_alerts": resolved_alerts,
        "false_positives": false_positives,
        "emails_sent": emails_sent,
        "tickets_created": tickets_created,
        "recent_alerts": recent_alerts,
        "period_days": days,
    }


def get_top_sources(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top alert sources."""
    result = db.query(
        Alert.source,
        func.count(Alert.id).label('count')
    ).filter(
        Alert.source.isnot(None)
    ).group_by(
        Alert.source
    ).order_by(
        desc('count')
    ).limit(limit).all()
    
    return [{"source": row.source, "count": row.count} for row in result]


def get_top_event_types(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top event types."""
    result = db.query(
        Alert.event_type,
        func.count(Alert.id).label('count')
    ).filter(
        Alert.event_type.isnot(None)
    ).group_by(
        Alert.event_type
    ).order_by(
        desc('count')
    ).limit(limit).all()
    
    return [{"event_type": row.event_type, "count": row.count} for row in result]


def get_top_ips(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top IP addresses."""
    result = db.query(
        Alert.ip,
        func.count(Alert.id).label('count')
    ).filter(
        Alert.ip.isnot(None)
    ).group_by(
        Alert.ip
    ).order_by(
        desc('count')
    ).limit(limit).all()
    
    return [{"ip": row.ip, "count": row.count} for row in result]
