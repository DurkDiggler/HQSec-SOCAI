"""Analytics and reporting microservice for SOC Agent."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..config import SETTINGS
from ..database import create_tables, get_db

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Service lifespan management."""
    # Startup
    logger.info("Starting Analytics Service...")
    
    # Create database tables
    create_tables()
    
    logger.info("Analytics Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Analytics Service...")

# Create FastAPI app
app = FastAPI(
    title="SOC Agent Analytics Service",
    description="Advanced analytics and reporting microservice",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_data(days: int = 7):
    """Get dashboard analytics data."""
    try:
        with get_db() as db:
            # Get alert statistics
            alert_stats = db.execute("""
                SELECT 
                    COUNT(*) as total_alerts,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '%s days' THEN 1 END) as recent_alerts,
                    COUNT(CASE WHEN status = 'new' THEN 1 END) as new_alerts,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_alerts,
                    AVG(final_score) as avg_score
                FROM alerts
            """, (days,)).fetchone()
            
            # Get top sources
            top_sources = db.execute("""
                SELECT source, COUNT(*) as count
                FROM alerts
                WHERE created_at > NOW() - INTERVAL '%s days'
                GROUP BY source
                ORDER BY count DESC
                LIMIT 10
            """, (days,)).fetchall()
            
            # Get severity distribution
            severity_dist = db.execute("""
                SELECT 
                    CASE 
                        WHEN final_score >= 70 THEN 'HIGH'
                        WHEN final_score >= 40 THEN 'MEDIUM'
                        ELSE 'LOW'
                    END as severity,
                    COUNT(*) as count
                FROM alerts
                WHERE created_at > NOW() - INTERVAL '%s days'
                GROUP BY 
                    CASE 
                        WHEN final_score >= 70 THEN 'HIGH'
                        WHEN final_score >= 40 THEN 'MEDIUM'
                        ELSE 'LOW'
                    END
            """, (days,)).fetchall()
            
            # Get hourly distribution
            hourly_dist = db.execute("""
                SELECT 
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as count
                FROM alerts
                WHERE created_at > NOW() - INTERVAL '%s days'
                GROUP BY EXTRACT(HOUR FROM created_at)
                ORDER BY hour
            """, (days,)).fetchall()
            
            return {
                "period_days": days,
                "alert_statistics": {
                    "total_alerts": alert_stats.total_alerts,
                    "recent_alerts": alert_stats.recent_alerts,
                    "new_alerts": alert_stats.new_alerts,
                    "resolved_alerts": alert_stats.resolved_alerts,
                    "average_score": float(alert_stats.avg_score) if alert_stats.avg_score else 0
                },
                "top_sources": [
                    {"source": row.source, "count": row.count}
                    for row in top_sources
                ],
                "severity_distribution": [
                    {"severity": row.severity, "count": row.count}
                    for row in severity_dist
                ],
                "hourly_distribution": [
                    {"hour": int(row.hour), "count": row.count}
                    for row in hourly_dist
                ]
            }
            
    except Exception as e:
        logger.error(f"Dashboard data retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard data retrieval failed: {str(e)}"
        )

@app.get("/api/v1/analytics/trends")
async def get_trends(
    metric: str = "alerts",
    period: str = "daily",
    days: int = 30
):
    """Get trend analysis."""
    try:
        with get_db() as db:
            if period == "daily":
                date_format = "%Y-%m-%d"
                group_by = "DATE(created_at)"
            elif period == "hourly":
                date_format = "%Y-%m-%d %H:00:00"
                group_by = "DATE_TRUNC('hour', created_at)"
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid period. Use 'daily' or 'hourly'"
                )
            
            if metric == "alerts":
                query = f"""
                    SELECT 
                        {group_by} as period,
                        COUNT(*) as count
                    FROM alerts
                    WHERE created_at > NOW() - INTERVAL '%s days'
                    GROUP BY {group_by}
                    ORDER BY period
                """
            elif metric == "incidents":
                query = f"""
                    SELECT 
                        {group_by} as period,
                        COUNT(*) as count
                    FROM incidents
                    WHERE created_at > NOW() - INTERVAL '%s days'
                    GROUP BY {group_by}
                    ORDER BY period
                """
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid metric. Use 'alerts' or 'incidents'"
                )
            
            trends = db.execute(query, (days,)).fetchall()
            
            return {
                "metric": metric,
                "period": period,
                "days": days,
                "data": [
                    {
                        "period": row.period.isoformat() if hasattr(row.period, 'isoformat') else str(row.period),
                        "count": row.count
                    }
                    for row in trends
                ]
            }
            
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trend analysis failed: {str(e)}"
        )

@app.post("/api/v1/reports/generate")
async def generate_report(report_config: Dict[str, Any]):
    """Generate custom report."""
    try:
        report_type = report_config.get("type", "summary")
        start_date = report_config.get("start_date")
        end_date = report_config.get("end_date")
        filters = report_config.get("filters", {})
        
        with get_db() as db:
            if report_type == "summary":
                # Generate summary report
                query = """
                    SELECT 
                        COUNT(*) as total_alerts,
                        COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved,
                        COUNT(CASE WHEN status = 'new' THEN 1 END) as new,
                        AVG(final_score) as avg_score,
                        MAX(created_at) as last_alert
                    FROM alerts
                    WHERE 1=1
                """
                params = []
                
                if start_date:
                    query += " AND created_at >= %s"
                    params.append(start_date)
                
                if end_date:
                    query += " AND created_at <= %s"
                    params.append(end_date)
                
                if filters.get("severity"):
                    query += " AND final_score >= %s"
                    params.append(filters["severity"])
                
                result = db.execute(query, params).fetchone()
                
                return {
                    "report_type": "summary",
                    "period": {
                        "start": start_date,
                        "end": end_date
                    },
                    "data": {
                        "total_alerts": result.total_alerts,
                        "resolved_alerts": result.resolved,
                        "new_alerts": result.new,
                        "average_score": float(result.avg_score) if result.avg_score else 0,
                        "last_alert": result.last_alert.isoformat() if result.last_alert else None
                    }
                }
            
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported report type"
                )
                
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Service health check."""
    try:
        # Check database connection
        with get_db() as db:
            db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "analytics-service",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.get("/metrics")
async def service_metrics():
    """Service metrics."""
    try:
        with get_db() as db:
            # Get report counts
            report_count = db.execute("SELECT COUNT(*) FROM reports").scalar()
            
            # Get recent reports (last 24 hours)
            recent_reports = db.execute("""
                SELECT COUNT(*) FROM reports 
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """).scalar()
            
            return {
                "service": "analytics-service",
                "metrics": {
                    "total_reports": report_count,
                    "recent_reports_24h": recent_reports
                }
            }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "service": "analytics-service",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
