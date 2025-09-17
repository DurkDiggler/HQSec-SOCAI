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
    ForeignKey,
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


class AIAnalysis(Base):
    """AI analysis results for alerts."""
    
    __tablename__ = "ai_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, index=True)
    
    # AI Analysis Results
    threat_classification = Column(String(100), nullable=True)
    risk_level = Column(String(20), nullable=True, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    confidence_score = Column(Float, default=0.0, index=True)
    
    # AI Insights
    ai_insights = Column(JSON, default=dict)
    recommendations = Column(JSON, default=list)
    attack_vectors = Column(JSON, default=list)
    iocs = Column(JSON, default=dict)
    mitigation_strategies = Column(JSON, default=list)
    pattern_analysis = Column(JSON, default=dict)
    
    # Metadata
    model_used = Column(String(50), nullable=True)
    processing_time = Column(Float, nullable=True)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert AI analysis to dictionary."""
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "threat_classification": self.threat_classification,
            "risk_level": self.risk_level,
            "confidence_score": self.confidence_score,
            "ai_insights": self.ai_insights,
            "recommendations": self.recommendations,
            "attack_vectors": self.attack_vectors,
            "iocs": self.iocs,
            "mitigation_strategies": self.mitigation_strategies,
            "pattern_analysis": self.pattern_analysis,
            "model_used": self.model_used,
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OffensiveTest(Base):
    """Offensive security test results."""
    
    __tablename__ = "offensive_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Test Details
    target = Column(String(255), nullable=False, index=True)
    test_type = Column(String(100), nullable=False, index=True)  # port_scan, vuln_scan, web_scan, etc.
    test_name = Column(String(255), nullable=True)
    
    # Test Status
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed, cancelled
    progress = Column(Integer, default=0)  # 0-100
    
    # Test Results
    results = Column(JSON, default=dict)
    findings = Column(JSON, default=list)
    vulnerabilities = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    
    # Test Configuration
    test_parameters = Column(JSON, default=dict)
    mcp_server_used = Column(String(100), nullable=True)
    
    # Authorization & Security
    authorized_by = Column(String(255), nullable=True)
    authorization_reason = Column(Text, nullable=True)
    test_scope = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # seconds
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert offensive test to dictionary."""
        return {
            "id": self.id,
            "target": self.target,
            "test_type": self.test_type,
            "test_name": self.test_name,
            "status": self.status,
            "progress": self.progress,
            "results": self.results,
            "findings": self.findings,
            "vulnerabilities": self.vulnerabilities,
            "recommendations": self.recommendations,
            "test_parameters": self.test_parameters,
            "mcp_server_used": self.mcp_server_used,
            "authorized_by": self.authorized_by,
            "authorization_reason": self.authorization_reason,
            "test_scope": self.test_scope,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ThreatCorrelation(Base):
    """Threat correlation analysis results."""
    
    __tablename__ = "threat_correlations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Correlation Details
    correlation_id = Column(String(100), nullable=False, unique=True, index=True)
    correlation_name = Column(String(255), nullable=False)
    correlation_type = Column(String(50), nullable=False, index=True)  # campaign, pattern, ioc_match
    
    # Related Alerts
    alert_ids = Column(JSON, default=list)  # List of related alert IDs
    
    # Correlation Analysis
    confidence_score = Column(Float, default=0.0, index=True)
    risk_level = Column(String(20), nullable=True, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    threat_actors = Column(JSON, default=list)
    attack_techniques = Column(JSON, default=list)
    ioc_matches = Column(JSON, default=dict)
    
    # Timeline
    first_seen = Column(DateTime, nullable=True, index=True)
    last_seen = Column(DateTime, nullable=True, index=True)
    duration_hours = Column(Float, nullable=True)
    
    # Status
    status = Column(String(50), default="active", index=True)  # active, monitoring, resolved, false_positive
    resolution_notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert threat correlation to dictionary."""
        return {
            "id": self.id,
            "correlation_id": self.correlation_id,
            "correlation_name": self.correlation_name,
            "correlation_type": self.correlation_type,
            "alert_ids": self.alert_ids,
            "confidence_score": self.confidence_score,
            "risk_level": self.risk_level,
            "threat_actors": self.threat_actors,
            "attack_techniques": self.attack_techniques,
            "ioc_matches": self.ioc_matches,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "duration_hours": self.duration_hours,
            "status": self.status,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


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
    # PostgreSQL configuration with connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections every hour
        echo=False  # Set to True for SQL debugging
    )

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


# AI Analysis Functions
def save_ai_analysis(
    db: Session,
    alert_id: int,
    ai_analysis: Dict[str, Any],
    model_used: str = None,
    processing_time: float = None
) -> AIAnalysis:
    """Save AI analysis results to database."""
    
    analysis = AIAnalysis(
        alert_id=alert_id,
        threat_classification=ai_analysis.get("threat_classification"),
        risk_level=ai_analysis.get("risk_level"),
        confidence_score=ai_analysis.get("confidence_score", 0.0),
        ai_insights=ai_analysis.get("ai_insights", {}),
        recommendations=ai_analysis.get("recommendations", []),
        attack_vectors=ai_analysis.get("attack_vectors", []),
        iocs=ai_analysis.get("iocs", {}),
        mitigation_strategies=ai_analysis.get("mitigation_strategies", []),
        pattern_analysis=ai_analysis.get("pattern_analysis", {}),
        model_used=model_used,
        processing_time=processing_time
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    return analysis


def get_ai_analysis_by_alert_id(db: Session, alert_id: int) -> Optional[AIAnalysis]:
    """Get AI analysis by alert ID."""
    return db.query(AIAnalysis).filter(AIAnalysis.alert_id == alert_id).first()


def get_ai_analyses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    risk_level: Optional[str] = None,
    min_confidence: Optional[float] = None
) -> List[AIAnalysis]:
    """Get AI analyses with filtering."""
    
    query = db.query(AIAnalysis)
    
    if risk_level:
        query = query.filter(AIAnalysis.risk_level == risk_level)
    if min_confidence is not None:
        query = query.filter(AIAnalysis.confidence_score >= min_confidence)
    
    return query.order_by(desc(AIAnalysis.created_at)).offset(skip).limit(limit).all()


# Offensive Test Functions
def save_offensive_test(
    db: Session,
    target: str,
    test_type: str,
    test_parameters: Dict[str, Any] = None,
    authorized_by: str = None,
    authorization_reason: str = None,
    test_scope: str = None
) -> OffensiveTest:
    """Save offensive test to database."""
    
    test = OffensiveTest(
        target=target,
        test_type=test_type,
        test_parameters=test_parameters or {},
        authorized_by=authorized_by,
        authorization_reason=authorization_reason,
        test_scope=test_scope,
        status="pending"
    )
    
    db.add(test)
    db.commit()
    db.refresh(test)
    
    return test


def update_offensive_test_status(
    db: Session,
    test_id: int,
    status: str,
    progress: int = None,
    results: Dict[str, Any] = None,
    findings: List[Dict[str, Any]] = None,
    vulnerabilities: List[Dict[str, Any]] = None,
    recommendations: List[str] = None,
    mcp_server_used: str = None
) -> Optional[OffensiveTest]:
    """Update offensive test status and results."""
    
    test = db.query(OffensiveTest).filter(OffensiveTest.id == test_id).first()
    if not test:
        return None
    
    test.status = status
    if progress is not None:
        test.progress = progress
    if results is not None:
        test.results = results
    if findings is not None:
        test.findings = findings
    if vulnerabilities is not None:
        test.vulnerabilities = vulnerabilities
    if recommendations is not None:
        test.recommendations = recommendations
    if mcp_server_used is not None:
        test.mcp_server_used = mcp_server_used
    
    # Update timing
    if status == "running" and not test.started_at:
        test.started_at = datetime.utcnow()
    elif status in ["completed", "failed", "cancelled"] and not test.completed_at:
        test.completed_at = datetime.utcnow()
        if test.started_at:
            test.duration = (test.completed_at - test.started_at).total_seconds()
    
    test.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(test)
    
    return test


def get_offensive_tests(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    test_type: Optional[str] = None,
    target: Optional[str] = None
) -> List[OffensiveTest]:
    """Get offensive tests with filtering."""
    
    query = db.query(OffensiveTest)
    
    if status:
        query = query.filter(OffensiveTest.status == status)
    if test_type:
        query = query.filter(OffensiveTest.test_type == test_type)
    if target:
        query = query.filter(OffensiveTest.target.ilike(f"%{target}%"))
    
    return query.order_by(desc(OffensiveTest.created_at)).offset(skip).limit(limit).all()


def get_offensive_test_by_id(db: Session, test_id: int) -> Optional[OffensiveTest]:
    """Get offensive test by ID."""
    return db.query(OffensiveTest).filter(OffensiveTest.id == test_id).first()


# Threat Correlation Functions
def save_threat_correlation(
    db: Session,
    correlation_id: str,
    correlation_name: str,
    correlation_type: str,
    alert_ids: List[int],
    confidence_score: float = 0.0,
    risk_level: str = None,
    threat_actors: List[str] = None,
    attack_techniques: List[str] = None,
    ioc_matches: Dict[str, Any] = None,
    first_seen: datetime = None,
    last_seen: datetime = None
) -> ThreatCorrelation:
    """Save threat correlation to database."""
    
    correlation = ThreatCorrelation(
        correlation_id=correlation_id,
        correlation_name=correlation_name,
        correlation_type=correlation_type,
        alert_ids=alert_ids,
        confidence_score=confidence_score,
        risk_level=risk_level,
        threat_actors=threat_actors or [],
        attack_techniques=attack_techniques or [],
        ioc_matches=ioc_matches or {},
        first_seen=first_seen,
        last_seen=last_seen
    )
    
    # Calculate duration if both timestamps are provided
    if first_seen and last_seen:
        correlation.duration_hours = (last_seen - first_seen).total_seconds() / 3600
    
    db.add(correlation)
    db.commit()
    db.refresh(correlation)
    
    return correlation


def get_threat_correlations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    correlation_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    min_confidence: Optional[float] = None
) -> List[ThreatCorrelation]:
    """Get threat correlations with filtering."""
    
    query = db.query(ThreatCorrelation)
    
    if status:
        query = query.filter(ThreatCorrelation.status == status)
    if correlation_type:
        query = query.filter(ThreatCorrelation.correlation_type == correlation_type)
    if risk_level:
        query = query.filter(ThreatCorrelation.risk_level == risk_level)
    if min_confidence is not None:
        query = query.filter(ThreatCorrelation.confidence_score >= min_confidence)
    
    return query.order_by(desc(ThreatCorrelation.created_at)).offset(skip).limit(limit).all()


def get_threat_correlation_by_id(db: Session, correlation_id: str) -> Optional[ThreatCorrelation]:
    """Get threat correlation by correlation ID."""
    return db.query(ThreatCorrelation).filter(ThreatCorrelation.correlation_id == correlation_id).first()


def update_threat_correlation_status(
    db: Session,
    correlation_id: str,
    status: str,
    resolution_notes: str = None
) -> Optional[ThreatCorrelation]:
    """Update threat correlation status."""
    
    correlation = db.query(ThreatCorrelation).filter(ThreatCorrelation.correlation_id == correlation_id).first()
    if not correlation:
        return None
    
    correlation.status = status
    if resolution_notes is not None:
        correlation.resolution_notes = resolution_notes
    correlation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(correlation)
    
    return correlation
