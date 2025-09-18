"""PostgreSQL clustering and replication for SOC Agent."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .config import SETTINGS

logger = logging.getLogger(__name__)

class DatabaseCluster:
    """PostgreSQL cluster management with master-slave replication."""
    
    def __init__(self):
        self.master_engine = None
        self.slave_engines = []
        self.connection_pools = {}
        self.health_status = {}
        self.last_health_check = 0
        self.health_check_interval = 30  # seconds
        
        # Initialize cluster
        self._initialize_cluster()
    
    def _initialize_cluster(self):
        """Initialize database cluster connections."""
        try:
            # Master database
            master_url = self._build_database_url(
                host=SETTINGS.postgres_host,
                port=SETTINGS.postgres_port,
                user=SETTINGS.postgres_user,
                password=SETTINGS.postgres_password,
                database=SETTINGS.postgres_db
            )
            
            self.master_engine = create_engine(
                master_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Slave databases (read replicas)
            slave_hosts = SETTINGS.postgres_slave_hosts or []
            for slave_host in slave_hosts:
                slave_url = self._build_database_url(
                    host=slave_host,
                    port=SETTINGS.postgres_port,
                    user=SETTINGS.postgres_user,
                    password=SETTINGS.postgres_password,
                    database=SETTINGS.postgres_db
                )
                
                slave_engine = create_engine(
                    slave_url,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=3600
                )
                
                self.slave_engines.append(slave_engine)
            
            # Create connection pools
            self._create_connection_pools()
            
            logger.info(f"Database cluster initialized: 1 master, {len(self.slave_engines)} slaves")
            
        except Exception as e:
            logger.error(f"Failed to initialize database cluster: {e}")
            raise
    
    def _build_database_url(self, host: str, port: int, user: str, 
                           password: str, database: str) -> str:
        """Build database URL."""
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def _create_connection_pools(self):
        """Create connection pools for each database."""
        try:
            # Master pool
            self.connection_pools["master"] = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                host=SETTINGS.postgres_host,
                port=SETTINGS.postgres_port,
                user=SETTINGS.postgres_user,
                password=SETTINGS.postgres_password,
                database=SETTINGS.postgres_db
            )
            
            # Slave pools
            slave_hosts = SETTINGS.postgres_slave_hosts or []
            for i, slave_host in enumerate(slave_hosts):
                pool_name = f"slave_{i}"
                self.connection_pools[pool_name] = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=slave_host,
                    port=SETTINGS.postgres_port,
                    user=SETTINGS.postgres_user,
                    password=SETTINGS.postgres_password,
                    database=SETTINGS.postgres_db
                )
            
            logger.info("Connection pools created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create connection pools: {e}")
            raise
    
    def get_master_engine(self):
        """Get master database engine."""
        return self.master_engine
    
    def get_slave_engine(self, index: int = 0):
        """Get slave database engine."""
        if not self.slave_engines:
            return self.master_engine
        
        if index >= len(self.slave_engines):
            index = 0
        
        return self.slave_engines[index]
    
    def get_read_engine(self):
        """Get engine for read operations (prefer slave)."""
        if self.slave_engines:
            return self.get_slave_engine()
        return self.master_engine
    
    def get_write_engine(self):
        """Get engine for write operations (always master)."""
        return self.master_engine
    
    @contextmanager
    def get_connection(self, read_only: bool = False):
        """Get database connection with automatic cleanup."""
        connection = None
        try:
            if read_only and self.slave_engines:
                # Use slave for read operations
                pool_name = "slave_0"  # Use first slave
                if pool_name in self.connection_pools:
                    connection = self.connection_pools[pool_name].getconn()
                else:
                    # Fallback to master
                    connection = self.connection_pools["master"].getconn()
            else:
                # Use master for write operations
                connection = self.connection_pools["master"].getconn()
            
            yield connection
            
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if connection:
                # Return connection to pool
                pool_name = "master"
                if read_only and "slave_0" in self.connection_pools:
                    pool_name = "slave_0"
                
                self.connection_pools[pool_name].putconn(connection)
    
    def check_health(self) -> Dict[str, Any]:
        """Check health of all database nodes."""
        current_time = time.time()
        
        # Skip if checked recently
        if current_time - self.last_health_check < self.health_check_interval:
            return self.health_status
        
        health_status = {
            "master": {"status": "unknown", "latency": 0, "last_check": current_time},
            "slaves": []
        }
        
        try:
            # Check master
            start_time = time.time()
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            
            master_latency = (time.time() - start_time) * 1000
            health_status["master"] = {
                "status": "healthy",
                "latency": master_latency,
                "last_check": current_time
            }
            
        except Exception as e:
            logger.error(f"Master database health check failed: {e}")
            health_status["master"] = {
                "status": "unhealthy",
                "error": str(e),
                "last_check": current_time
            }
        
        # Check slaves
        for i, slave_engine in enumerate(self.slave_engines):
            try:
                start_time = time.time()
                with slave_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                slave_latency = (time.time() - start_time) * 1000
                health_status["slaves"].append({
                    "index": i,
                    "status": "healthy",
                    "latency": slave_latency,
                    "last_check": current_time
                })
                
            except Exception as e:
                logger.error(f"Slave {i} database health check failed: {e}")
                health_status["slaves"].append({
                    "index": i,
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": current_time
                })
        
        self.health_status = health_status
        self.last_health_check = current_time
        
        return health_status
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get overall cluster status."""
        health = self.check_health()
        
        master_healthy = health["master"]["status"] == "healthy"
        healthy_slaves = [s for s in health["slaves"] if s["status"] == "healthy"]
        
        return {
            "cluster_status": "healthy" if master_healthy and len(healthy_slaves) > 0 else "degraded",
            "master_status": health["master"]["status"],
            "slave_count": len(self.slave_engines),
            "healthy_slaves": len(healthy_slaves),
            "total_connections": sum(
                pool.closed + pool.overflow for pool in self.connection_pools.values()
            ),
            "health_check": health
        }
    
    def execute_read_query(self, query: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """Execute read query on slave database."""
        try:
            with self.get_connection(read_only=True) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"Read query failed: {e}")
            raise
    
    def execute_write_query(self, query: str, params: Tuple = None) -> int:
        """Execute write query on master database."""
        try:
            with self.get_connection(read_only=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Write query failed: {e}")
            raise
    
    def close_all_connections(self):
        """Close all database connections."""
        try:
            # Close connection pools
            for pool_name, pool in self.connection_pools.items():
                pool.closeall()
            
            # Close engines
            if self.master_engine:
                self.master_engine.dispose()
            
            for slave_engine in self.slave_engines:
                slave_engine.dispose()
            
            logger.info("All database connections closed")
            
        except Exception as e:
            logger.error(f"Failed to close database connections: {e}")

class DatabaseReplication:
    """Database replication management."""
    
    def __init__(self, cluster: DatabaseCluster):
        self.cluster = cluster
    
    def check_replication_lag(self) -> Dict[str, Any]:
        """Check replication lag between master and slaves."""
        try:
            # Get master WAL position
            with self.cluster.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT pg_current_wal_lsn()")
                    master_lsn = cursor.fetchone()[0]
            
            replication_status = {
                "master_lsn": master_lsn,
                "slaves": []
            }
            
            # Check each slave
            for i, slave_engine in enumerate(self.cluster.slave_engines):
                try:
                    with slave_engine.connect() as conn:
                        result = conn.execute(text("""
                            SELECT 
                                pg_last_wal_receive_lsn() as received_lsn,
                                pg_last_wal_replay_lsn() as replayed_lsn,
                                pg_wal_lsn_diff(pg_current_wal_lsn(), pg_last_wal_receive_lsn()) as receive_lag,
                                pg_wal_lsn_diff(pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn()) as replay_lag
                        """))
                        
                        row = result.fetchone()
                        if row:
                            replication_status["slaves"].append({
                                "index": i,
                                "received_lsn": str(row.received_lsn),
                                "replayed_lsn": str(row.replayed_lsn),
                                "receive_lag_bytes": row.receive_lag,
                                "replay_lag_bytes": row.replay_lag,
                                "status": "healthy" if row.receive_lag < 1000000 else "lagging"
                            })
                
                except Exception as e:
                    logger.error(f"Failed to check replication lag for slave {i}: {e}")
                    replication_status["slaves"].append({
                        "index": i,
                        "status": "error",
                        "error": str(e)
                    })
            
            return replication_status
            
        except Exception as e:
            logger.error(f"Failed to check replication lag: {e}")
            return {"error": str(e)}

# Global cluster instance
db_cluster = DatabaseCluster()
replication_manager = DatabaseReplication(db_cluster)
