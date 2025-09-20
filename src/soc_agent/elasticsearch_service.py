"""Elasticsearch service for log aggregation and search."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

from .config import SETTINGS

logger = logging.getLogger(__name__)


class ElasticsearchError(Exception):
    """Elasticsearch related errors."""
    pass


class ElasticsearchService:
    """Elasticsearch service for log aggregation and search."""
    
    def __init__(self):
        self.client = None
        self.index_prefix = SETTINGS.elasticsearch_index_prefix
        self.retention_days = SETTINGS.elasticsearch_log_retention_days
        
        if SETTINGS.elasticsearch_enabled:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Elasticsearch client."""
        try:
            # Build connection parameters
            connection_params = {
                'hosts': [f"{SETTINGS.elasticsearch_host}:{SETTINGS.elasticsearch_port}"],
                'timeout': 30,
                'max_retries': 3,
                'retry_on_timeout': True
            }
            
            # Add authentication if configured
            if SETTINGS.elasticsearch_username and SETTINGS.elasticsearch_password:
                connection_params['basic_auth'] = (
                    SETTINGS.elasticsearch_username,
                    SETTINGS.elasticsearch_password
                )
            
            # Add SSL configuration
            if SETTINGS.elasticsearch_use_ssl:
                connection_params['use_ssl'] = True
                connection_params['verify_certs'] = SETTINGS.elasticsearch_verify_certs
                if SETTINGS.elasticsearch_ca_certs:
                    connection_params['ca_certs'] = SETTINGS.elasticsearch_ca_certs
            
            self.client = Elasticsearch(**connection_params)
            
            # Test connection
            if not self.client.ping():
                raise ElasticsearchError("Failed to connect to Elasticsearch")
            
            # Create default indices
            self._create_default_indices()
            
        except Exception as e:
            raise ElasticsearchError(f"Failed to initialize Elasticsearch: {str(e)}")
    
    def _create_default_indices(self):
        """Create default indices with proper mappings."""
        indices = {
            'audit_logs': self._get_audit_logs_mapping(),
            'system_logs': self._get_system_logs_mapping(),
            'security_events': self._get_security_events_mapping(),
            'performance_metrics': self._get_performance_metrics_mapping()
        }
        
        for index_name, mapping in indices.items():
            full_index_name = f"{self.index_prefix}-{index_name}"
            self._create_index_if_not_exists(full_index_name, mapping)
    
    def _get_audit_logs_mapping(self) -> Dict[str, Any]:
        """Get mapping for audit logs index."""
        return {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "user_id": {"type": "integer"},
                    "session_id": {"type": "keyword"},
                    "ip_address": {"type": "ip"},
                    "user_agent": {"type": "text", "analyzer": "standard"},
                    "event_type": {"type": "keyword"},
                    "event_category": {"type": "keyword"},
                    "resource_type": {"type": "keyword"},
                    "resource_id": {"type": "keyword"},
                    "action": {"type": "keyword"},
                    "description": {"type": "text", "analyzer": "standard"},
                    "details": {"type": "object"},
                    "risk_level": {"type": "keyword"},
                    "security_context": {"type": "object"},
                    "compliance_tags": {"type": "keyword"},
                    "data_classification": {"type": "keyword"},
                    "success": {"type": "boolean"},
                    "error_code": {"type": "keyword"},
                    "error_message": {"type": "text"},
                    "duration_ms": {"type": "integer"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.lifecycle.name": f"{self.index_prefix}-audit-logs-policy",
                "index.lifecycle.rollover_alias": f"{self.index_prefix}-audit-logs"
            }
        }
    
    def _get_system_logs_mapping(self) -> Dict[str, Any]:
        """Get mapping for system logs index."""
        return {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "level": {"type": "keyword"},
                    "logger": {"type": "keyword"},
                    "message": {"type": "text", "analyzer": "standard"},
                    "module": {"type": "keyword"},
                    "function": {"type": "keyword"},
                    "line_number": {"type": "integer"},
                    "thread": {"type": "keyword"},
                    "process_id": {"type": "integer"},
                    "hostname": {"type": "keyword"},
                    "service": {"type": "keyword"},
                    "environment": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "extra": {"type": "object"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.lifecycle.name": f"{self.index_prefix}-system-logs-policy",
                "index.lifecycle.rollover_alias": f"{self.index_prefix}-system-logs"
            }
        }
    
    def _get_security_events_mapping(self) -> Dict[str, Any]:
        """Get mapping for security events index."""
        return {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "event_id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "event_type": {"type": "keyword"},
                    "severity": {"type": "integer"},
                    "category": {"type": "keyword"},
                    "description": {"type": "text", "analyzer": "standard"},
                    "ip_address": {"type": "ip"},
                    "user": {"type": "keyword"},
                    "hostname": {"type": "keyword"},
                    "process": {"type": "keyword"},
                    "file_path": {"type": "keyword"},
                    "file_hash": {"type": "keyword"},
                    "network": {"type": "object"},
                    "iocs": {"type": "object"},
                    "threat_indicators": {"type": "object"},
                    "raw_data": {"type": "object"},
                    "tags": {"type": "keyword"},
                    "risk_score": {"type": "float"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.lifecycle.name": f"{self.index_prefix}-security-events-policy",
                "index.lifecycle.rollover_alias": f"{self.index_prefix}-security-events"
            }
        }
    
    def _get_performance_metrics_mapping(self) -> Dict[str, Any]:
        """Get mapping for performance metrics index."""
        return {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "metric_name": {"type": "keyword"},
                    "metric_value": {"type": "float"},
                    "metric_unit": {"type": "keyword"},
                    "service": {"type": "keyword"},
                    "hostname": {"type": "keyword"},
                    "environment": {"type": "keyword"},
                    "tags": {"type": "object"},
                    "metadata": {"type": "object"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.lifecycle.name": f"{self.index_prefix}-performance-metrics-policy",
                "index.lifecycle.rollover_alias": f"{self.index_prefix}-performance-metrics"
            }
        }
    
    def _create_index_if_not_exists(self, index_name: str, mapping: Dict[str, Any]):
        """Create index if it doesn't exist."""
        try:
            if not self.client.indices.exists(index=index_name):
                self.client.indices.create(index=index_name, body=mapping)
                logger.info(f"Created Elasticsearch index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {str(e)}")
    
    def index_document(self, index_name: str, document: Dict[str, Any], 
                      doc_id: Optional[str] = None) -> str:
        """Index a document in Elasticsearch."""
        if not self.client:
            raise ElasticsearchError("Elasticsearch not initialized")
        
        try:
            full_index_name = f"{self.index_prefix}-{index_name}"
            
            # Add timestamp if not present
            if 'timestamp' not in document:
                document['timestamp'] = datetime.utcnow().isoformat()
            
            response = self.client.index(
                index=full_index_name,
                body=document,
                id=doc_id
            )
            
            return response['_id']
        except Exception as e:
            raise ElasticsearchError(f"Failed to index document: {str(e)}")
    
    def bulk_index(self, index_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk index multiple documents."""
        if not self.client:
            raise ElasticsearchError("Elasticsearch not initialized")
        
        try:
            full_index_name = f"{self.index_prefix}-{index_name}"
            
            # Prepare bulk data
            bulk_data = []
            for doc in documents:
                # Add timestamp if not present
                if 'timestamp' not in doc:
                    doc['timestamp'] = datetime.utcnow().isoformat()
                
                bulk_data.append({
                    "index": {
                        "_index": full_index_name
                    }
                })
                bulk_data.append(doc)
            
            response = self.client.bulk(body=bulk_data)
            return response
        except Exception as e:
            raise ElasticsearchError(f"Failed to bulk index documents: {str(e)}")
    
    def search(self, index_name: str, query: Dict[str, Any], 
              size: int = 100, from_: int = 0) -> Dict[str, Any]:
        """Search documents in Elasticsearch."""
        if not self.client:
            raise ElasticsearchError("Elasticsearch not initialized")
        
        try:
            full_index_name = f"{self.index_prefix}-{index_name}"
            
            response = self.client.search(
                index=full_index_name,
                body=query,
                size=size,
                from_=from_
            )
            
            return response
        except Exception as e:
            raise ElasticsearchError(f"Failed to search documents: {str(e)}")
    
    def get_document(self, index_name: str, doc_id: str) -> Dict[str, Any]:
        """Get a specific document by ID."""
        if not self.client:
            raise ElasticsearchError("Elasticsearch not initialized")
        
        try:
            full_index_name = f"{self.index_prefix}-{index_name}"
            
            response = self.client.get(
                index=full_index_name,
                id=doc_id
            )
            
            return response['_source']
        except NotFoundError:
            raise ElasticsearchError(f"Document {doc_id} not found")
        except Exception as e:
            raise ElasticsearchError(f"Failed to get document: {str(e)}")
    
    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """Delete a document by ID."""
        if not self.client:
            raise ElasticsearchError("Elasticsearch not initialized")
        
        try:
            full_index_name = f"{self.index_prefix}-{index_name}"
            
            response = self.client.delete(
                index=full_index_name,
                id=doc_id
            )
            
            return response['result'] == 'deleted'
        except Exception as e:
            raise ElasticsearchError(f"Failed to delete document: {str(e)}")
    
    def search_audit_logs(self, query: Dict[str, Any], size: int = 100, 
                         from_: int = 0) -> Dict[str, Any]:
        """Search audit logs with common query patterns."""
        return self.search('audit_logs', query, size, from_)
    
    def search_system_logs(self, query: Dict[str, Any], size: int = 100, 
                          from_: int = 0) -> Dict[str, Any]:
        """Search system logs with common query patterns."""
        return self.search('system_logs', query, size, from_)
    
    def search_security_events(self, query: Dict[str, Any], size: int = 100, 
                              from_: int = 0) -> Dict[str, Any]:
        """Search security events with common query patterns."""
        return self.search('security_events', query, size, from_)
    
    def search_performance_metrics(self, query: Dict[str, Any], size: int = 100, 
                                  from_: int = 0) -> Dict[str, Any]:
        """Search performance metrics with common query patterns."""
        return self.search('performance_metrics', query, size, from_)
    
    def get_cluster_health(self) -> Dict[str, Any]:
        """Get Elasticsearch cluster health."""
        if not self.client:
            raise ElasticsearchError("Elasticsearch not initialized")
        
        try:
            return self.client.cluster.health()
        except Exception as e:
            raise ElasticsearchError(f"Failed to get cluster health: {str(e)}")
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get index statistics."""
        if not self.client:
            raise ElasticsearchError("Elasticsearch not initialized")
        
        try:
            full_index_name = f"{self.index_prefix}-{index_name}"
            return self.client.indices.stats(index=full_index_name)
        except Exception as e:
            raise ElasticsearchError(f"Failed to get index stats: {str(e)}")
    
    def cleanup_old_indices(self, days: int = None) -> int:
        """Clean up old indices based on retention policy."""
        if not self.client:
            raise ElasticsearchError("Elasticsearch not initialized")
        
        if days is None:
            days = self.retention_days
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cutoff_str = cutoff_date.strftime("%Y.%m.%d")
            
            # Get all indices
            response = self.client.cat.indices(format='json')
            
            deleted_count = 0
            for index in response:
                index_name = index['index']
                if (index_name.startswith(self.index_prefix) and 
                    index_name < f"{self.index_prefix}-{cutoff_str}"):
                    self.client.indices.delete(index=index_name)
                    deleted_count += 1
            
            return deleted_count
        except Exception as e:
            raise ElasticsearchError(f"Failed to cleanup old indices: {str(e)}")
    
    def create_search_query(self, search_term: str = "", filters: Dict[str, Any] = None,
                           date_range: Dict[str, str] = None, sort: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a search query with common patterns."""
        query = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            }
        }
        
        # Add search term
        if search_term:
            query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": search_term,
                    "fields": ["*"],
                    "type": "best_fields"
                }
            })
        
        # Add filters
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    query["query"]["bool"]["filter"].append({
                        "terms": {field: value}
                    })
                else:
                    query["query"]["bool"]["filter"].append({
                        "term": {field: value}
                    })
        
        # Add date range
        if date_range:
            query["query"]["bool"]["filter"].append({
                "range": {
                    "timestamp": {
                        "gte": date_range.get("from"),
                        "lte": date_range.get("to")
                    }
                }
            })
        
        # Add sorting
        if sort:
            query["sort"] = sort
        else:
            query["sort"] = [{"timestamp": {"order": "desc"}}]
        
        return query


# Global Elasticsearch service instance
elasticsearch_service = ElasticsearchService()


def index_audit_log(audit_log: Dict[str, Any]) -> str:
    """Index audit log in Elasticsearch."""
    return elasticsearch_service.index_document('audit_logs', audit_log)


def index_system_log(log_data: Dict[str, Any]) -> str:
    """Index system log in Elasticsearch."""
    return elasticsearch_service.index_document('system_logs', log_data)


def index_security_event(event_data: Dict[str, Any]) -> str:
    """Index security event in Elasticsearch."""
    return elasticsearch_service.index_document('security_events', event_data)


def index_performance_metric(metric_data: Dict[str, Any]) -> str:
    """Index performance metric in Elasticsearch."""
    return elasticsearch_service.index_document('performance_metrics', metric_data)


def search_logs(index_name: str, query: Dict[str, Any], size: int = 100, 
                from_: int = 0) -> Dict[str, Any]:
    """Search logs in Elasticsearch."""
    return elasticsearch_service.search(index_name, query, size, from_)
