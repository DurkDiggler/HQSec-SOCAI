"""Time-series database service for metrics and telemetry."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.rest import ApiException

from .config import SETTINGS

logger = logging.getLogger(__name__)


class TimeSeriesError(Exception):
    """Time-series database related errors."""
    pass


class TimeSeriesService:
    """Time-series database service for metrics and telemetry."""
    
    def __init__(self):
        self.client = None
        self.write_api = None
        self.query_api = None
        self.org = SETTINGS.timeseries_org
        self.bucket = SETTINGS.timeseries_bucket
        self.retention_days = SETTINGS.timeseries_retention_days
        self.batch_size = SETTINGS.timeseries_batch_size
        self.flush_interval = SETTINGS.timeseries_flush_interval
        
        # Batch writing
        self.batch_buffer = []
        self.last_flush = time.time()
        
        if SETTINGS.timeseries_enabled:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize InfluxDB client."""
        try:
            self.client = InfluxDBClient(
                url=SETTINGS.timeseries_url,
                token=SETTINGS.timeseries_token,
                org=self.org,
                timeout=30000
            )
            
            # Test connection
            if not self.client.ping():
                raise TimeSeriesError("Failed to connect to InfluxDB")
            
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            
            # Create bucket if it doesn't exist
            self._ensure_bucket_exists()
            
        except ApiException as e:
            raise TimeSeriesError(f"Failed to initialize InfluxDB: {str(e)}")
        except Exception as e:
            raise TimeSeriesError(f"Failed to initialize time-series database: {str(e)}")
    
    def _ensure_bucket_exists(self):
        """Ensure the time-series bucket exists."""
        try:
            buckets_api = self.client.buckets_api()
            buckets = buckets_api.find_buckets()
            
            bucket_exists = any(bucket.name == self.bucket for bucket in buckets)
            
            if not bucket_exists:
                # Create bucket with retention policy
                retention_rule = {
                    "type": "expire",
                    "everySeconds": self.retention_days * 24 * 60 * 60
                }
                
                buckets_api.create_bucket(
                    bucket_name=self.bucket,
                    org=self.org,
                    retention_rules=[retention_rule]
                )
                logger.info(f"Created InfluxDB bucket: {self.bucket}")
            
        except ApiException as e:
            raise TimeSeriesError(f"Failed to create bucket: {str(e)}")
    
    def write_point(self, measurement: str, fields: Dict[str, Any], 
                   tags: Optional[Dict[str, str]] = None, 
                   timestamp: Optional[datetime] = None) -> bool:
        """Write a single data point to InfluxDB."""
        if not self.write_api:
            raise TimeSeriesError("Time-series database not initialized")
        
        try:
            point = Point(measurement)
            
            # Add tags
            if tags:
                for key, value in tags.items():
                    point = point.tag(key, value)
            
            # Add fields
            for key, value in fields.items():
                if isinstance(value, (int, float)):
                    point = point.field(key, value)
                elif isinstance(value, bool):
                    point = point.field(key, value)
                elif isinstance(value, str):
                    point = point.field(key, value)
            
            # Set timestamp
            if timestamp:
                point = point.time(timestamp, WritePrecision.NS)
            else:
                point = point.time(datetime.utcnow(), WritePrecision.NS)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
            
        except ApiException as e:
            raise TimeSeriesError(f"Failed to write point: {str(e)}")
    
    def write_points(self, points: List[Point]) -> bool:
        """Write multiple data points to InfluxDB."""
        if not self.write_api:
            raise TimeSeriesError("Time-series database not initialized")
        
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            return True
        except ApiException as e:
            raise TimeSeriesError(f"Failed to write points: {str(e)}")
    
    def batch_write_point(self, measurement: str, fields: Dict[str, Any], 
                         tags: Optional[Dict[str, str]] = None, 
                         timestamp: Optional[datetime] = None) -> bool:
        """Add point to batch buffer for later writing."""
        try:
            point = Point(measurement)
            
            # Add tags
            if tags:
                for key, value in tags.items():
                    point = point.tag(key, value)
            
            # Add fields
            for key, value in fields.items():
                if isinstance(value, (int, float)):
                    point = point.field(key, value)
                elif isinstance(value, bool):
                    point = point.field(key, value)
                elif isinstance(value, str):
                    point = point.field(key, value)
            
            # Set timestamp
            if timestamp:
                point = point.time(timestamp, WritePrecision.NS)
            else:
                point = point.time(datetime.utcnow(), WritePrecision.NS)
            
            self.batch_buffer.append(point)
            
            # Flush if buffer is full or time interval reached
            if (len(self.batch_buffer) >= self.batch_size or 
                time.time() - self.last_flush >= self.flush_interval):
                self.flush_batch()
            
            return True
            
        except Exception as e:
            raise TimeSeriesError(f"Failed to add point to batch: {str(e)}")
    
    def flush_batch(self) -> bool:
        """Flush the batch buffer to InfluxDB."""
        if not self.batch_buffer:
            return True
        
        if not self.write_api:
            raise TimeSeriesError("Time-series database not initialized")
        
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=self.batch_buffer)
            self.batch_buffer.clear()
            self.last_flush = time.time()
            return True
        except ApiException as e:
            raise TimeSeriesError(f"Failed to flush batch: {str(e)}")
    
    def query_data(self, query: str) -> List[Dict[str, Any]]:
        """Query data from InfluxDB."""
        if not self.query_api:
            raise TimeSeriesError("Time-series database not initialized")
        
        try:
            result = self.query_api.query(org=self.org, query=query)
            
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        'measurement': record.get_measurement(),
                        'field': record.get_field(),
                        'value': record.get_value(),
                        'time': record.get_time(),
                        'tags': record.values
                    })
            
            return data
        except ApiException as e:
            raise TimeSeriesError(f"Failed to query data: {str(e)}")
    
    def get_metrics_summary(self, measurement: str, 
                           time_range: str = "1h") -> Dict[str, Any]:
        """Get metrics summary for a measurement."""
        query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "{measurement}")
        |> group(columns: ["_field"])
        |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
        |> yield(name: "summary")
        '''
        
        try:
            data = self.query_data(query)
            
            summary = {}
            for record in data:
                field = record['field']
                if field not in summary:
                    summary[field] = []
                summary[field].append(record['value'])
            
            # Calculate statistics
            result = {}
            for field, values in summary.items():
                if values:
                    result[field] = {
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'count': len(values),
                        'latest': values[-1] if values else None
                    }
            
            return result
        except Exception as e:
            raise TimeSeriesError(f"Failed to get metrics summary: {str(e)}")
    
    def get_time_series_data(self, measurement: str, field: str, 
                           time_range: str = "1h", 
                           tags: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Get time series data for a specific measurement and field."""
        query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "{measurement}")
        |> filter(fn: (r) => r._field == "{field}")
        '''
        
        if tags:
            for key, value in tags.items():
                query += f'|> filter(fn: (r) => r.{key} == "{value}")\n'
        
        query += '|> yield(name: "time_series")'
        
        try:
            return self.query_data(query)
        except Exception as e:
            raise TimeSeriesError(f"Failed to get time series data: {str(e)}")
    
    def record_performance_metric(self, metric_name: str, value: float, 
                                 unit: str = "", tags: Optional[Dict[str, str]] = None) -> bool:
        """Record a performance metric."""
        fields = {'value': value}
        if unit:
            fields['unit'] = unit
        
        return self.batch_write_point('performance_metrics', fields, tags)
    
    def record_system_metric(self, metric_name: str, value: float, 
                           tags: Optional[Dict[str, str]] = None) -> bool:
        """Record a system metric."""
        fields = {'value': value}
        tags = tags or {}
        tags['metric_name'] = metric_name
        
        return self.batch_write_point('system_metrics', fields, tags)
    
    def record_security_metric(self, metric_name: str, value: float, 
                             tags: Optional[Dict[str, str]] = None) -> bool:
        """Record a security metric."""
        fields = {'value': value}
        tags = tags or {}
        tags['metric_name'] = metric_name
        
        return self.batch_write_point('security_metrics', fields, tags)
    
    def record_api_metric(self, endpoint: str, method: str, status_code: int, 
                         response_time: float, tags: Optional[Dict[str, str]] = None) -> bool:
        """Record an API metric."""
        fields = {
            'response_time': response_time,
            'status_code': status_code
        }
        
        tags = tags or {}
        tags.update({
            'endpoint': endpoint,
            'method': method
        })
        
        return self.batch_write_point('api_metrics', fields, tags)
    
    def record_alert_metric(self, alert_type: str, severity: int, 
                           tags: Optional[Dict[str, str]] = None) -> bool:
        """Record an alert metric."""
        fields = {
            'severity': severity,
            'count': 1
        }
        
        tags = tags or {}
        tags['alert_type'] = alert_type
        
        return self.batch_write_point('alert_metrics', fields, tags)
    
    def get_dashboard_metrics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Get dashboard metrics for the specified time range."""
        try:
            # Get performance metrics
            perf_query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: -{time_range})
            |> filter(fn: (r) => r._measurement == "performance_metrics")
            |> group(columns: ["_field"])
            |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
            |> yield(name: "performance")
            '''
            
            # Get API metrics
            api_query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: -{time_range})
            |> filter(fn: (r) => r._measurement == "api_metrics")
            |> group(columns: ["_field"])
            |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
            |> yield(name: "api")
            '''
            
            # Get alert metrics
            alert_query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: -{time_range})
            |> filter(fn: (r) => r._measurement == "alert_metrics")
            |> group(columns: ["_field"])
            |> aggregateWindow(every: 1h, fn: sum, createEmpty: false)
            |> yield(name: "alerts")
            '''
            
            performance_data = self.query_data(perf_query)
            api_data = self.query_data(api_query)
            alert_data = self.query_data(alert_query)
            
            return {
                'performance': self._process_metrics_data(performance_data),
                'api': self._process_metrics_data(api_data),
                'alerts': self._process_metrics_data(alert_data)
            }
            
        except Exception as e:
            raise TimeSeriesError(f"Failed to get dashboard metrics: {str(e)}")
    
    def _process_metrics_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process metrics data for dashboard display."""
        result = {}
        
        for record in data:
            field = record['field']
            value = record['value']
            time = record['time']
            
            if field not in result:
                result[field] = []
            
            result[field].append({
                'time': time,
                'value': value
            })
        
        return result
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get time-series database health status."""
        try:
            if not self.client:
                return {'status': 'disconnected', 'error': 'Client not initialized'}
            
            # Test connection
            if not self.client.ping():
                return {'status': 'disconnected', 'error': 'Connection failed'}
            
            # Get bucket info
            buckets_api = self.client.buckets_api()
            bucket = buckets_api.find_bucket_by_name(self.bucket)
            
            return {
                'status': 'connected',
                'bucket': self.bucket,
                'org': self.org,
                'retention_days': self.retention_days,
                'batch_size': self.batch_size,
                'buffer_size': len(self.batch_buffer)
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}


# Global time-series service instance
timeseries_service = TimeSeriesService()


def record_metric(measurement: str, fields: Dict[str, Any], 
                 tags: Optional[Dict[str, str]] = None) -> bool:
    """Record a metric in the time-series database."""
    return timeseries_service.batch_write_point(measurement, fields, tags)


def record_performance_metric(metric_name: str, value: float, 
                            unit: str = "", tags: Optional[Dict[str, str]] = None) -> bool:
    """Record a performance metric."""
    return timeseries_service.record_performance_metric(metric_name, value, unit, tags)


def record_api_metric(endpoint: str, method: str, status_code: int, 
                     response_time: float, tags: Optional[Dict[str, str]] = None) -> bool:
    """Record an API metric."""
    return timeseries_service.record_api_metric(endpoint, method, status_code, response_time, tags)


def record_alert_metric(alert_type: str, severity: int, 
                       tags: Optional[Dict[str, str]] = None) -> bool:
    """Record an alert metric."""
    return timeseries_service.record_alert_metric(alert_type, severity, tags)


def get_dashboard_metrics(time_range: str = "24h") -> Dict[str, Any]:
    """Get dashboard metrics."""
    return timeseries_service.get_dashboard_metrics(time_range)
