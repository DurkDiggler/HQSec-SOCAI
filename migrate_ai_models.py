#!/usr/bin/env python3
"""
Database migration script to add AI and offensive testing models.
Run this script to upgrade your existing SOC Agent database.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from soc_agent.database import create_tables, engine
from soc_agent.config import SETTINGS
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Create new tables for AI and offensive testing models."""
    try:
        logger.info("Starting database migration...")
        logger.info(f"Database URL: {SETTINGS.database_url}")
        
        # Create all tables (this will only create new ones)
        create_tables()
        
        logger.info("✅ Database migration completed successfully!")
        logger.info("New tables created:")
        logger.info("  - ai_analyses (AI analysis results)")
        logger.info("  - offensive_tests (Offensive security test results)")
        logger.info("  - threat_correlations (Threat correlation analysis)")
        
        # Test the connection
        with engine.connect() as conn:
            result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in result]
            logger.info(f"Current tables in database: {', '.join(tables)}")
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        sys.exit(1)

def verify_migration():
    """Verify that the migration was successful."""
    try:
        from sqlalchemy import inspect
        from soc_agent.database import AIAnalysis, OffensiveTest, ThreatCorrelation
        
        inspector = inspect(engine)
        
        # Check if new tables exist
        tables = inspector.get_table_names()
        required_tables = ['ai_analyses', 'offensive_tests', 'threat_correlations']
        
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            logger.error(f"❌ Migration verification failed. Missing tables: {missing_tables}")
            return False
        
        logger.info("✅ Migration verification passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SOC Agent Database Migration")
    print("=" * 40)
    
    # Check if we're using SQLite (for development)
    if SETTINGS.database_url.startswith('sqlite'):
        print("📝 Note: You're using SQLite. This migration will modify your local database.")
        print("   Make sure to backup your data if needed.")
        print()
    
    # Confirm migration
    response = input("Do you want to proceed with the migration? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Migration cancelled.")
        sys.exit(0)
    
    # Run migration
    migrate_database()
    
    # Verify migration
    if verify_migration():
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart your SOC Agent service")
        print("2. Configure your OpenAI API key in .env file")
        print("3. Start the Kali MCP server")
        print("4. Test the new AI and MCP features in the web interface")
    else:
        print("\n❌ Migration verification failed. Please check the logs above.")
        sys.exit(1)
