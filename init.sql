-- PostgreSQL initialization script for SOC Agent
-- Database and user are created by Docker environment variables
-- This script runs after the database is created

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
-- (These will be created by SQLAlchemy, but we can add custom ones here)

-- Create a view for recent high-severity alerts
CREATE OR REPLACE VIEW recent_high_severity_alerts AS
SELECT 
    id,
    source,
    event_type,
    severity,
    timestamp,
    message,
    ip,
    category,
    status,
    created_at
FROM alerts 
WHERE severity >= 7 
    AND created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Create a view for alert statistics
CREATE OR REPLACE VIEW alert_statistics_view AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_alerts,
    COUNT(CASE WHEN severity >= 7 THEN 1 END) as high_severity,
    COUNT(CASE WHEN severity >= 4 AND severity < 7 THEN 1 END) as medium_severity,
    COUNT(CASE WHEN severity < 4 THEN 1 END) as low_severity,
    COUNT(CASE WHEN status = 'new' THEN 1 END) as new_alerts,
    COUNT(CASE WHEN status = 'acknowledged' THEN 1 END) as acknowledged_alerts,
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_alerts,
    COUNT(CASE WHEN status = 'false_positive' THEN 1 END) as false_positives,
    COUNT(CASE WHEN email_sent = true THEN 1 END) as emails_sent,
    COUNT(CASE WHEN ticket_created = true THEN 1 END) as tickets_created
FROM alerts 
GROUP BY DATE(created_at)
ORDER BY date DESC;
