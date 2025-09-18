#!/usr/bin/env python3
"""
Database Performance Migration Script

This script applies enterprise-level database performance optimizations including:
- Comprehensive indexing for all tables
- GIN indexes for JSON columns (PostgreSQL)
- Connection pool optimization
- Query performance monitoring setup
"""

import os
import sys
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from soc_agent.database import create_tables, get_database_metrics, optimize_database
from soc_agent.config import SETTINGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run database performance migration."""
    logger.info("Starting database performance migration...")
    
    try:
        # Create tables with new indexes
        logger.info("Creating tables with optimized indexes...")
        create_tables()
        logger.info("✓ Tables created successfully")
        
        # Run database optimization
        logger.info("Running database optimization...")
        optimize_database()
        logger.info("✓ Database optimization completed")
        
        # Get initial metrics
        logger.info("Collecting initial performance metrics...")
        metrics = get_database_metrics()
        logger.info(f"✓ Initial metrics collected: {metrics['query_count']} queries, {metrics['avg_query_time']:.3f}s avg")
        
        logger.info("🎉 Database performance migration completed successfully!")
        
        # Print summary
        print("\n" + "="*60)
        print("DATABASE PERFORMANCE MIGRATION SUMMARY")
        print("="*60)
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print(f"Database: {SETTINGS.database_url}")
        print(f"Connection Pool Size: {metrics['connection_pool_stats']['pool_size']}")
        print(f"Total Queries: {metrics['query_count']}")
        print(f"Average Query Time: {metrics['avg_query_time']:.3f}s")
        print(f"Slow Queries: {len(metrics['slow_queries'])}")
        print("\nOptimizations Applied:")
        print("✓ Comprehensive indexing on all tables")
        print("✓ Composite indexes for common query patterns")
        print("✓ GIN indexes for JSON columns (PostgreSQL)")
        print("✓ Connection pool optimization")
        print("✓ Query performance monitoring")
        print("✓ Database statistics collection")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
