"""Add performance indexes

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes to improve query performance."""
    
    # Alert table indexes
    op.create_index('idx_alerts_timestamp_severity', 'alerts', ['timestamp', 'severity'])
    op.create_index('idx_alerts_source_event_type', 'alerts', ['source', 'event_type'])
    op.create_index('idx_alerts_category_status', 'alerts', ['category', 'status'])
    op.create_index('idx_alerts_created_at', 'alerts', ['created_at'])
    op.create_index('idx_alerts_updated_at', 'alerts', ['updated_at'])
    
    # User table indexes
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_username', 'users', ['username'], unique=True)
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_last_login', 'users', ['last_login'])
    
    # Role table indexes
    op.create_index('idx_roles_name', 'roles', ['name'], unique=True)
    op.create_index('idx_roles_is_system_role', 'roles', ['is_system_role'])
    
    # UserRole table indexes
    op.create_index('idx_user_roles_user_id', 'user_roles', ['user_id'])
    op.create_index('idx_user_roles_role_id', 'user_roles', ['role_id'])
    op.create_index('idx_user_roles_user_role', 'user_roles', ['user_id', 'role_id'], unique=True)
    
    # AuditLog table indexes
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('idx_audit_logs_user_timestamp', 'audit_logs', ['user_id', 'timestamp'])
    
    # AIAnalysis table indexes
    op.create_index('idx_ai_analyses_alert_id', 'ai_analyses', ['alert_id'])
    op.create_index('idx_ai_analyses_risk_level', 'ai_analyses', ['risk_level'])
    op.create_index('idx_ai_analyses_confidence', 'ai_analyses', ['confidence'])
    op.create_index('idx_ai_analyses_created_at', 'ai_analyses', ['created_at'])
    
    # OffensiveTest table indexes
    op.create_index('idx_offensive_tests_target', 'offensive_tests', ['target'])
    op.create_index('idx_offensive_tests_status', 'offensive_tests', ['status'])
    op.create_index('idx_offensive_tests_test_type', 'offensive_tests', ['test_type'])
    op.create_index('idx_offensive_tests_created_at', 'offensive_tests', ['created_at'])
    
    # ThreatCorrelation table indexes
    op.create_index('idx_threat_correlations_correlation_type', 'threat_correlations', ['correlation_type'])
    op.create_index('idx_threat_correlations_risk_level', 'threat_correlations', ['risk_level'])
    op.create_index('idx_threat_correlations_confidence', 'threat_correlations', ['confidence'])
    op.create_index('idx_threat_correlations_created_at', 'threat_correlations', ['created_at'])
    
    # StorageFile table indexes
    op.create_index('idx_storage_files_bucket_name', 'storage_files', ['bucket_name'])
    op.create_index('idx_storage_files_is_public', 'storage_files', ['is_public'])
    op.create_index('idx_storage_files_file_hash', 'storage_files', ['file_hash'])
    op.create_index('idx_storage_files_created_at', 'storage_files', ['created_at'])
    op.create_index('idx_storage_files_last_accessed', 'storage_files', ['last_accessed'])


def downgrade():
    """Remove performance indexes."""
    
    # Remove all indexes in reverse order
    op.drop_index('idx_storage_files_last_accessed', 'storage_files')
    op.drop_index('idx_storage_files_created_at', 'storage_files')
    op.drop_index('idx_storage_files_file_hash', 'storage_files')
    op.drop_index('idx_storage_files_is_public', 'storage_files')
    op.drop_index('idx_storage_files_bucket_name', 'storage_files')
    
    op.drop_index('idx_threat_correlations_created_at', 'threat_correlations')
    op.drop_index('idx_threat_correlations_confidence', 'threat_correlations')
    op.drop_index('idx_threat_correlations_risk_level', 'threat_correlations')
    op.drop_index('idx_threat_correlations_correlation_type', 'threat_correlations')
    
    op.drop_index('idx_offensive_tests_created_at', 'offensive_tests')
    op.drop_index('idx_offensive_tests_test_type', 'offensive_tests')
    op.drop_index('idx_offensive_tests_status', 'offensive_tests')
    op.drop_index('idx_offensive_tests_target', 'offensive_tests')
    
    op.drop_index('idx_ai_analyses_created_at', 'ai_analyses')
    op.drop_index('idx_ai_analyses_confidence', 'ai_analyses')
    op.drop_index('idx_ai_analyses_risk_level', 'ai_analyses')
    op.drop_index('idx_ai_analyses_alert_id', 'ai_analyses')
    
    op.drop_index('idx_audit_logs_user_timestamp', 'audit_logs')
    op.drop_index('idx_audit_logs_resource_type', 'audit_logs')
    op.drop_index('idx_audit_logs_timestamp', 'audit_logs')
    op.drop_index('idx_audit_logs_action', 'audit_logs')
    op.drop_index('idx_audit_logs_user_id', 'audit_logs')
    
    op.drop_index('idx_user_roles_user_role', 'user_roles')
    op.drop_index('idx_user_roles_role_id', 'user_roles')
    op.drop_index('idx_user_roles_user_id', 'user_roles')
    
    op.drop_index('idx_roles_is_system_role', 'roles')
    op.drop_index('idx_roles_name', 'roles')
    
    op.drop_index('idx_users_last_login', 'users')
    op.drop_index('idx_users_is_active', 'users')
    op.drop_index('idx_users_username', 'users')
    op.drop_index('idx_users_email', 'users')
    
    op.drop_index('idx_alerts_updated_at', 'alerts')
    op.drop_index('idx_alerts_created_at', 'alerts')
    op.drop_index('idx_alerts_category_status', 'alerts')
    op.drop_index('idx_alerts_source_event_type', 'alerts')
    op.drop_index('idx_alerts_timestamp_severity', 'alerts')
