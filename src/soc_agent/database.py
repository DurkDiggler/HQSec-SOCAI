"""Database models and connection management for SOC Agent."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager

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
    Index,
    event,
    text,
    Table,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session, relationship
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select

from .config import SETTINGS

# Configure logging
logger = logging.getLogger(__name__)

Base = declarative_base()

# Database performance monitoring
class DatabaseMetrics:
    """Database performance metrics collector."""
    
    def __init__(self):
        self.query_count = 0
        self.total_query_time = 0.0
        self.slow_queries = []
        self.connection_pool_stats = {}
    
    def record_query(self, query_time: float, query: str = None):
        """Record query performance metrics."""
        self.query_count += 1
        self.total_query_time += query_time
        
        if query_time > 1.0:  # Slow query threshold
            self.slow_queries.append({
                'query': query[:100] if query else 'Unknown',
                'execution_time': query_time,
                'timestamp': datetime.utcnow()
            })
    
    def get_avg_query_time(self) -> float:
        """Get average query execution time."""
        return self.total_query_time / self.query_count if self.query_count > 0 else 0.0
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """Get recent slow queries."""
        return sorted(self.slow_queries, key=lambda x: x['execution_time'], reverse=True)[:limit]

# Global metrics instance
db_metrics = DatabaseMetrics()


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
    
    # Composite indexes for common query patterns
    __table_args__ = (
        # Index for dashboard queries (status + timestamp)
        Index('idx_alerts_status_timestamp', 'status', 'timestamp'),
        # Index for severity-based filtering
        Index('idx_alerts_severity_timestamp', 'severity', 'timestamp'),
        # Index for source-based analysis
        Index('idx_alerts_source_timestamp', 'source', 'timestamp'),
        # Index for IP-based queries
        Index('idx_alerts_ip_timestamp', 'ip', 'timestamp'),
        # Index for category-based filtering
        Index('idx_alerts_category_timestamp', 'category', 'timestamp'),
        # Index for assigned user queries
        Index('idx_alerts_assigned_timestamp', 'assigned_to', 'timestamp'),
        # Index for score-based filtering
        Index('idx_alerts_final_score_timestamp', 'final_score', 'timestamp'),
        # Index for time-based queries
        Index('idx_alerts_created_at', 'created_at'),
        # Index for updated_at queries
        Index('idx_alerts_updated_at', 'updated_at'),
        # Index for email/ticket status queries
        Index('idx_alerts_actions', 'email_sent', 'ticket_created'),
        # Index for event type analysis
        Index('idx_alerts_event_type_timestamp', 'event_type', 'timestamp'),
    )
    
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
    
    # Indexes for time-based queries
    __table_args__ = (
        Index('idx_alert_stats_date', 'date'),
        Index('idx_alert_stats_date_desc', 'date', postgresql_using='btree'),
    )


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
    
    # Indexes for AI analysis queries
    __table_args__ = (
        # Index for risk level filtering
        Index('idx_ai_analyses_risk_level_created', 'risk_level', 'created_at'),
        # Index for confidence score filtering
        Index('idx_ai_analyses_confidence_created', 'confidence_score', 'created_at'),
        # Index for threat classification analysis
        Index('idx_ai_analyses_classification_created', 'threat_classification', 'created_at'),
        # Index for model performance analysis
        Index('idx_ai_analyses_model_created', 'model_used', 'created_at'),
        # Index for processing time analysis
        Index('idx_ai_analyses_processing_time', 'processing_time'),
        # Index for alert relationship queries
        Index('idx_ai_analyses_alert_id_created', 'alert_id', 'created_at'),
    )
    
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
    
    # Indexes for offensive test queries
    __table_args__ = (
        # Index for status-based filtering
        Index('idx_offensive_tests_status_created', 'status', 'created_at'),
        # Index for test type analysis
        Index('idx_offensive_tests_type_created', 'test_type', 'created_at'),
        # Index for target-based queries
        Index('idx_offensive_tests_target_created', 'target', 'created_at'),
        # Index for authorization tracking
        Index('idx_offensive_tests_authorized_by', 'authorized_by'),
        # Index for MCP server analysis
        Index('idx_offensive_tests_mcp_server', 'mcp_server_used'),
        # Index for duration analysis
        Index('idx_offensive_tests_duration', 'duration'),
        # Index for progress tracking
        Index('idx_offensive_tests_progress', 'progress'),
    )
    
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
    
    # Indexes for threat correlation queries
    __table_args__ = (
        # Index for status-based filtering
        Index('idx_threat_correlations_status_created', 'status', 'created_at'),
        # Index for correlation type analysis
        Index('idx_threat_correlations_type_created', 'correlation_type', 'created_at'),
        # Index for risk level filtering
        Index('idx_threat_correlations_risk_level_created', 'risk_level', 'created_at'),
        # Index for confidence score filtering
        Index('idx_threat_correlations_confidence_created', 'confidence_score', 'created_at'),
        # Index for timeline analysis
        Index('idx_threat_correlations_timeline', 'first_seen', 'last_seen'),
        # Index for duration analysis
        Index('idx_threat_correlations_duration', 'duration_hours'),
        # Index for correlation ID lookups
        Index('idx_threat_correlations_correlation_id', 'correlation_id'),
    )
    
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


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', Integer, ForeignKey('users.id')),
    Index('idx_user_roles_user_id', 'user_id'),
    Index('idx_user_roles_role_id', 'role_id'),
)


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    full_name = Column(String(255), nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False, index=True)
    last_login = Column(DateTime, nullable=True, index=True)
    
    # OAuth Integration
    oauth_provider = Column(String(50), nullable=True, index=True)  # google, microsoft, etc.
    oauth_id = Column(String(255), nullable=True, index=True)
    oauth_data = Column(JSON, default=dict)
    
    # MFA
    mfa_enabled = Column(Boolean, default=False, index=True)
    mfa_secret = Column(String(32), nullable=True)  # TOTP secret
    mfa_backup_codes = Column(JSON, default=list)  # List of backup codes
    
    # Profile
    avatar_url = Column(String(500), nullable=True)
    department = Column(String(100), nullable=True, index=True)
    job_title = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    password_changed_at = Column(DateTime, nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    # Indexes
    __table_args__ = (
        Index('idx_users_email_active', 'email', 'is_active'),
        Index('idx_users_username_active', 'username', 'is_active'),
        Index('idx_users_oauth', 'oauth_provider', 'oauth_id'),
        Index('idx_users_department', 'department'),
        Index('idx_users_created_at', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "oauth_provider": self.oauth_provider,
            "mfa_enabled": self.mfa_enabled,
            "avatar_url": self.avatar_url,
            "department": self.department,
            "job_title": self.job_title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Role(Base):
    """Role model for RBAC."""
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Permissions (stored as JSON for flexibility)
    permissions = Column(JSON, default=list)  # List of permission strings
    
    # Role hierarchy
    is_system_role = Column(Boolean, default=False, index=True)  # System roles cannot be deleted
    parent_role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    parent_role = relationship("Role", remote_side=[id])
    
    # Indexes
    __table_args__ = (
        Index('idx_roles_name_active', 'name', 'is_active'),
        Index('idx_roles_system', 'is_system_role'),
        Index('idx_roles_parent', 'parent_role_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "permissions": self.permissions,
            "is_system_role": self.is_system_role,
            "parent_role_id": self.parent_role_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AuditLog(Base):
    """Enhanced audit logging for compliance."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User and Session Information
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    
    # Event Details
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, create, update, delete, etc.
    event_category = Column(String(50), nullable=False, index=True)  # auth, data, system, security
    resource_type = Column(String(50), nullable=True, index=True)  # alert, user, role, etc.
    resource_id = Column(String(100), nullable=True, index=True)
    
    # Event Description
    action = Column(String(100), nullable=False, index=True)  # specific action taken
    description = Column(Text, nullable=True)
    details = Column(JSON, default=dict)  # Additional event details
    
    # Security Context
    risk_level = Column(String(20), nullable=True, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    security_context = Column(JSON, default=dict)  # Security-related metadata
    
    # Compliance Fields
    compliance_tags = Column(JSON, default=list)  # SOX, GDPR, HIPAA, etc.
    data_classification = Column(String(20), nullable=True, index=True)  # public, internal, confidential, restricted
    
    # Result and Status
    success = Column(Boolean, nullable=False, index=True)
    error_code = Column(String(50), nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    duration_ms = Column(Integer, nullable=True)  # Event duration in milliseconds
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes for compliance and security queries
    __table_args__ = (
        # Time-based queries
        Index('idx_audit_logs_timestamp', 'timestamp'),
        Index('idx_audit_logs_user_timestamp', 'user_id', 'timestamp'),
        # Event-based queries
        Index('idx_audit_logs_event_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_audit_logs_event_category_timestamp', 'event_category', 'timestamp'),
        # Resource-based queries
        Index('idx_audit_logs_resource_timestamp', 'resource_type', 'resource_id', 'timestamp'),
        # Security queries
        Index('idx_audit_logs_risk_level_timestamp', 'risk_level', 'timestamp'),
        Index('idx_audit_logs_ip_timestamp', 'ip_address', 'timestamp'),
        # Compliance queries
        Index('idx_audit_logs_compliance_timestamp', 'compliance_tags', 'timestamp'),
        Index('idx_audit_logs_data_classification_timestamp', 'data_classification', 'timestamp'),
        # Success/failure analysis
        Index('idx_audit_logs_success_timestamp', 'success', 'timestamp'),
        # Session tracking
        Index('idx_audit_logs_session_timestamp', 'session_id', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "event_type": self.event_type,
            "event_category": self.event_category,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "description": self.description,
            "details": self.details,
            "risk_level": self.risk_level,
            "security_context": self.security_context,
            "compliance_tags": self.compliance_tags,
            "data_classification": self.data_classification,
            "success": self.success,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "duration_ms": self.duration_ms,
        }


class StorageFile(Base):
    """Storage file metadata model."""
    
    __tablename__ = "storage_files"
    
    id = Column(Integer, primary_key=True, index=True)
    object_key = Column(String(500), nullable=False, unique=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    folder = Column(String(100), nullable=False, index=True)
    size = Column(Integer, nullable=False, index=True)
    content_type = Column(String(100), nullable=True, index=True)
    
    # Storage metadata
    storage_provider = Column(String(50), nullable=False, index=True)
    bucket_name = Column(String(100), nullable=False, index=True)
    public_url = Column(String(1000), nullable=True)
    
    # File metadata
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash
    file_metadata = Column(JSON, default=dict)
    
    # Access control
    is_public = Column(Boolean, default=False, index=True)
    access_count = Column(Integer, default=0, index=True)
    last_accessed = Column(DateTime, nullable=True, index=True)
    
    # Ownership
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    uploader = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_storage_files_object_key', 'object_key'),
        Index('idx_storage_files_filename', 'filename'),
        Index('idx_storage_files_folder', 'folder'),
        Index('idx_storage_files_size', 'size'),
        Index('idx_storage_files_uploaded_by', 'uploaded_by'),
        Index('idx_storage_files_created_at', 'created_at'),
        Index('idx_storage_files_is_public', 'is_public'),
        Index('idx_storage_files_storage_provider', 'storage_provider'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert storage file to dictionary."""
        return {
            "id": self.id,
            "object_key": self.object_key,
            "filename": self.filename,
            "folder": self.folder,
            "size": self.size,
            "content_type": self.content_type,
            "storage_provider": self.storage_provider,
            "bucket_name": self.bucket_name,
            "public_url": self.public_url,
            "file_hash": self.file_hash,
            "metadata": self.metadata,
            "is_public": self.is_public,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ElasticsearchIndex(Base):
    """Elasticsearch index metadata model."""
    
    __tablename__ = "elasticsearch_indices"
    
    id = Column(Integer, primary_key=True, index=True)
    index_name = Column(String(100), nullable=False, unique=True, index=True)
    index_type = Column(String(50), nullable=False, index=True)  # audit_logs, system_logs, etc.
    document_count = Column(Integer, default=0, index=True)
    index_size_bytes = Column(Integer, default=0, index=True)
    
    # Index configuration
    mapping = Column(JSON, default=dict)
    settings = Column(JSON, default=dict)
    
    # Lifecycle management
    retention_days = Column(Integer, default=30, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync = Column(DateTime, nullable=True, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_elasticsearch_indices_name', 'index_name'),
        Index('idx_elasticsearch_indices_type', 'index_type'),
        Index('idx_elasticsearch_indices_active', 'is_active'),
        Index('idx_elasticsearch_indices_created_at', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Elasticsearch index to dictionary."""
        return {
            "id": self.id,
            "index_name": self.index_name,
            "index_type": self.index_type,
            "document_count": self.document_count,
            "index_size_bytes": self.index_size_bytes,
            "mapping": self.mapping,
            "settings": self.settings,
            "retention_days": self.retention_days,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
        }


class TimeSeriesMetric(Base):
    """Time-series metric metadata model."""
    
    __tablename__ = "timeseries_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    measurement = Column(String(100), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    
    # Metric configuration
    unit = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=dict)
    
    # Statistics
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    avg_value = Column(Float, nullable=True)
    count = Column(Integer, default=0, index=True)
    
    # Time range
    first_seen = Column(DateTime, nullable=True, index=True)
    last_seen = Column(DateTime, nullable=True, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_timeseries_metrics_name', 'metric_name'),
        Index('idx_timeseries_metrics_measurement', 'measurement'),
        Index('idx_timeseries_metrics_field', 'field_name'),
        Index('idx_timeseries_metrics_active', 'is_active'),
        Index('idx_timeseries_metrics_first_seen', 'first_seen'),
        Index('idx_timeseries_metrics_last_seen', 'last_seen'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert time-series metric to dictionary."""
        return {
            "id": self.id,
            "metric_name": self.metric_name,
            "measurement": self.measurement,
            "field_name": self.field_name,
            "unit": self.unit,
            "description": self.description,
            "tags": self.tags,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "avg_value": self.avg_value,
            "count": self.count,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Enhanced connection pooling configuration
def get_database_url():
    """Get database URL from settings."""
    if SETTINGS.postgres_host and SETTINGS.postgres_user and SETTINGS.postgres_password and SETTINGS.postgres_db:
        return f"postgresql://{SETTINGS.postgres_user}:{SETTINGS.postgres_password}@{SETTINGS.postgres_host}:{SETTINGS.postgres_port}/{SETTINGS.postgres_db}"
    return SETTINGS.database_url

DATABASE_URL = get_database_url()

# Enhanced engine configuration with enterprise-level settings
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=SETTINGS.log_level == "DEBUG",
        echo_pool=SETTINGS.log_level == "DEBUG",
    )
else:
    # PostgreSQL configuration with enterprise-level connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,  # Base pool size
        max_overflow=30,  # Additional connections when needed
        pool_pre_ping=True,  # Validate connections before use
        pool_recycle=3600,  # Recycle connections every hour
        pool_timeout=30,  # Timeout for getting connection from pool
        pool_reset_on_return='commit',  # Reset connections on return
        echo=SETTINGS.log_level == "DEBUG",
        echo_pool=SETTINGS.log_level == "DEBUG",
        # Performance optimizations
        connect_args={
            "options": "-c default_transaction_isolation=read_committed",
            "application_name": "soc_agent",
            "connect_timeout": 10,
        }
    )

# Enhanced session configuration
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent lazy loading issues
)

# Scoped session for thread safety
ScopedSession = scoped_session(SessionLocal)

# Query performance monitoring
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time."""
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query execution time."""
    if hasattr(context, '_query_start_time'):
        query_time = time.time() - context._query_start_time
        db_metrics.record_query(query_time, statement)

# Enhanced database session management
@contextmanager
def get_db_session():
    """Enhanced database session context manager with error handling."""
    session = ScopedSession()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        session.close()


def create_tables():
    """Create all database tables with optimized indexes."""
    Base.metadata.create_all(bind=engine)
    
    # Create additional performance indexes for PostgreSQL
    if not DATABASE_URL.startswith('sqlite'):
        with engine.connect() as conn:
            # Create GIN indexes for JSON columns (PostgreSQL only)
            try:
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_iocs_gin 
                    ON alerts USING GIN (iocs);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_intel_data_gin 
                    ON alerts USING GIN (intel_data);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_raw_data_gin 
                    ON alerts USING GIN (raw_data);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_analyses_ai_insights_gin 
                    ON ai_analyses USING GIN (ai_insights);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_analyses_recommendations_gin 
                    ON ai_analyses USING GIN (recommendations);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_analyses_attack_vectors_gin 
                    ON ai_analyses USING GIN (attack_vectors);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_analyses_iocs_gin 
                    ON ai_analyses USING GIN (iocs);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_analyses_mitigation_strategies_gin 
                    ON ai_analyses USING GIN (mitigation_strategies);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_analyses_pattern_analysis_gin 
                    ON ai_analyses USING GIN (pattern_analysis);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_offensive_tests_results_gin 
                    ON offensive_tests USING GIN (results);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_offensive_tests_findings_gin 
                    ON offensive_tests USING GIN (findings);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_offensive_tests_vulnerabilities_gin 
                    ON offensive_tests USING GIN (vulnerabilities);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_offensive_tests_recommendations_gin 
                    ON offensive_tests USING GIN (recommendations);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_offensive_tests_test_parameters_gin 
                    ON offensive_tests USING GIN (test_parameters);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_threat_correlations_alert_ids_gin 
                    ON threat_correlations USING GIN (alert_ids);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_threat_correlations_threat_actors_gin 
                    ON threat_correlations USING GIN (threat_actors);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_threat_correlations_attack_techniques_gin 
                    ON threat_correlations USING GIN (attack_techniques);
                """))
                conn.execute(text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_threat_correlations_ioc_matches_gin 
                    ON threat_correlations USING GIN (ioc_matches);
                """))
                conn.commit()
                logger.info("Created GIN indexes for JSON columns")
            except Exception as e:
                logger.warning(f"Could not create GIN indexes: {e}")

def get_database_metrics() -> Dict[str, Any]:
    """Get database performance metrics."""
    return {
        "query_count": db_metrics.query_count,
        "total_query_time": db_metrics.total_query_time,
        "avg_query_time": db_metrics.get_avg_query_time(),
        "slow_queries": db_metrics.get_slow_queries(),
        "connection_pool_stats": {
            "pool_size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "invalid": engine.pool.invalid(),
        }
    }

def optimize_database():
    """Run database optimization tasks."""
    if DATABASE_URL.startswith('sqlite'):
        # SQLite optimization
        with engine.connect() as conn:
            conn.execute(text("PRAGMA optimize;"))
            conn.execute(text("VACUUM;"))
            logger.info("SQLite database optimized")
    else:
        # PostgreSQL optimization
        with engine.connect() as conn:
            # Update table statistics
            conn.execute(text("ANALYZE;"))
            # Reindex if needed (run during maintenance window)
            # conn.execute(text("REINDEX DATABASE soc_agent;"))
            logger.info("PostgreSQL database optimized")

def get_query_plan(query: str) -> Dict[str, Any]:
    """Get query execution plan for optimization."""
    if DATABASE_URL.startswith('sqlite'):
        with engine.connect() as conn:
            result = conn.execute(text(f"EXPLAIN QUERY PLAN {query}"))
            return {"plan": [dict(row) for row in result]}
    else:
        with engine.connect() as conn:
            result = conn.execute(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"))
            return {"plan": result.fetchone()[0]}

def get_table_statistics() -> Dict[str, Any]:
    """Get table statistics for monitoring."""
    stats = {}
    
    with engine.connect() as conn:
        if DATABASE_URL.startswith('sqlite'):
            # SQLite table info
            for table_name in ['alerts', 'ai_analyses', 'offensive_tests', 'threat_correlations']:
                result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table_name}"))
                count = result.fetchone()[0]
                stats[table_name] = {"row_count": count}
        else:
            # PostgreSQL table statistics
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables 
                WHERE tablename IN ('alerts', 'ai_analyses', 'offensive_tests', 'threat_correlations')
                ORDER BY tablename;
            """))
            stats = {row[1]: dict(row._mapping) for row in result}
    
    return stats


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
    """Get alerts with filtering and pagination - optimized for performance."""
    
    # Use select for better performance
    query = db.query(Alert)
    
    # Apply filters with proper indexing
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
    
    # Order by timestamp descending (uses index)
    query = query.order_by(desc(Alert.timestamp))
    
    # Apply pagination
    return query.offset(skip).limit(limit).all()

def get_alerts_optimized(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    severity: Optional[int] = None,
    source: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get alerts with advanced optimization and metadata."""
    
    # Build optimized query
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
    if start_date:
        query = query.filter(Alert.timestamp >= start_date)
    if end_date:
        query = query.filter(Alert.timestamp <= end_date)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Alert.message.ilike(search_term)) |
            (Alert.ip.ilike(search_term)) |
            (Alert.username.ilike(search_term)) |
            (Alert.event_type.ilike(search_term))
        )
    
    # Get total count for pagination
    total_count = query.count()
    
    # Apply ordering and pagination
    alerts = query.order_by(desc(Alert.timestamp)).offset(skip).limit(limit).all()
    
    return {
        "alerts": alerts,
        "total_count": total_count,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "total_pages": (total_count + limit - 1) // limit
    }


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
