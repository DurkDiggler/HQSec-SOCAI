"""Real-time stream analytics and monitoring for AI processing."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS

logger = logging.getLogger(__name__)

class StreamAnalytics:
    """
    Real-time analytics and monitoring for stream processing pipeline.
    Provides metrics, alerts, and insights on AI processing performance.
    """

    def __init__(self):
        self.metrics_buffer: List[Dict[str, Any]] = []
        self.alert_counts: Dict[str, int] = {}
        self.performance_metrics: Dict[str, List[float]] = {}
        self.throughput_metrics: Dict[str, List[int]] = {}
        self.latency_metrics: Dict[str, List[float]] = {}
        self.running = False

    async def start_analytics(self):
        """Starts the stream analytics monitoring."""
        self.running = True
        logger.info("Starting stream analytics monitoring...")
        
        # Start background analytics tasks
        asyncio.create_task(self._metrics_aggregation_loop())
        asyncio.create_task(self._performance_monitoring_loop())
        asyncio.create_task(self._anomaly_detection_loop())

    async def stop_analytics(self):
        """Stops the stream analytics monitoring."""
        self.running = False
        logger.info("Stream analytics monitoring stopped")

    async def record_event(self, 
                          event_type: str,
                          processing_time: float,
                          model_name: str = None,
                          success: bool = True,
                          metadata: Dict[str, Any] = None):
        """
        Records an event for analytics.
        
        Args:
            event_type: Type of event (prediction, training, error, etc.)
            processing_time: Time taken to process the event
            model_name: Name of the model used
            success: Whether the event was successful
            metadata: Additional metadata
        """
        event_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "processing_time": processing_time,
            "model_name": model_name,
            "success": success,
            "metadata": metadata or {}
        }
        
        self.metrics_buffer.append(event_record)
        
        # Update performance metrics
        if model_name:
            if model_name not in self.performance_metrics:
                self.performance_metrics[model_name] = []
            self.performance_metrics[model_name].append(processing_time)
            
            # Keep only last N metrics
            max_metrics = 1000
            if len(self.performance_metrics[model_name]) > max_metrics:
                self.performance_metrics[model_name] = self.performance_metrics[model_name][-max_metrics:]
        
        # Update throughput metrics
        if event_type not in self.throughput_metrics:
            self.throughput_metrics[event_type] = []
        
        current_time = datetime.utcnow()
        minute_key = current_time.strftime("%Y-%m-%d %H:%M")
        
        # Count events per minute
        if minute_key not in self.throughput_metrics[event_type]:
            self.throughput_metrics[event_type] = []
        
        # This is simplified - in production, you'd have proper time windowing
        self.throughput_metrics[event_type].append(1)
        
        # Keep only last hour of throughput data
        if len(self.throughput_metrics[event_type]) > 60:
            self.throughput_metrics[event_type] = self.throughput_metrics[event_type][-60:]

    async def record_prediction(self, 
                               model_name: str,
                               processing_time: float,
                               prediction_confidence: float,
                               success: bool = True):
        """Records a prediction event."""
        await self.record_event(
            event_type="prediction",
            processing_time=processing_time,
            model_name=model_name,
            success=success,
            metadata={"confidence": prediction_confidence}
        )

    async def record_training(self, 
                             model_name: str,
                             training_time: float,
                             data_size: int,
                             success: bool = True):
        """Records a training event."""
        await self.record_event(
            event_type="training",
            processing_time=training_time,
            model_name=model_name,
            success=success,
            metadata={"data_size": data_size}
        )

    async def record_error(self, 
                          error_type: str,
                          model_name: str = None,
                          error_message: str = None):
        """Records an error event."""
        await self.record_event(
            event_type="error",
            processing_time=0.0,
            model_name=model_name,
            success=False,
            metadata={"error_type": error_type, "error_message": error_message}
        )

    async def _metrics_aggregation_loop(self):
        """Background loop for aggregating metrics."""
        while self.running:
            try:
                await asyncio.sleep(60)  # Aggregate every minute
                
                if self.metrics_buffer:
                    await self._aggregate_metrics()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics aggregation loop: {e}")

    async def _aggregate_metrics(self):
        """Aggregates metrics from the buffer."""
        if not self.metrics_buffer:
            return
        
        # Group metrics by time window (minute)
        current_time = datetime.utcnow()
        minute_window = current_time.replace(second=0, microsecond=0)
        
        # Filter metrics for current minute
        recent_metrics = [
            m for m in self.metrics_buffer
            if datetime.fromisoformat(m["timestamp"]).replace(second=0, microsecond=0) == minute_window
        ]
        
        if not recent_metrics:
            return
        
        # Calculate aggregated metrics
        total_events = len(recent_metrics)
        successful_events = sum(1 for m in recent_metrics if m["success"])
        error_events = total_events - successful_events
        
        # Calculate average processing time
        avg_processing_time = np.mean([m["processing_time"] for m in recent_metrics])
        
        # Calculate throughput (events per minute)
        throughput = total_events
        
        # Store aggregated metrics
        aggregated_metric = {
            "timestamp": minute_window.isoformat(),
            "total_events": total_events,
            "successful_events": successful_events,
            "error_events": error_events,
            "success_rate": successful_events / total_events if total_events > 0 else 0,
            "avg_processing_time": avg_processing_time,
            "throughput": throughput
        }
        
        logger.info(f"Metrics aggregated: {aggregated_metric}")
        
        # Clear processed metrics from buffer
        self.metrics_buffer = [m for m in self.metrics_buffer 
                              if datetime.fromisoformat(m["timestamp"]).replace(second=0, microsecond=0) != minute_window]

    async def _performance_monitoring_loop(self):
        """Background loop for monitoring performance."""
        while self.running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                await self._check_performance_thresholds()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}")

    async def _check_performance_thresholds(self):
        """Checks if performance metrics exceed thresholds."""
        for model_name, processing_times in self.performance_metrics.items():
            if not processing_times:
                continue
            
            # Calculate performance metrics
            avg_latency = np.mean(processing_times)
            p95_latency = np.percentile(processing_times, 95)
            p99_latency = np.percentile(processing_times, 99)
            
            # Check thresholds
            if avg_latency > SETTINGS.performance_degradation_threshold:
                logger.warning(f"High average latency for {model_name}: {avg_latency:.3f}s")
                await self._trigger_performance_alert(model_name, "high_latency", avg_latency)
            
            if p95_latency > SETTINGS.performance_degradation_threshold * 2:
                logger.warning(f"High P95 latency for {model_name}: {p95_latency:.3f}s")
                await self._trigger_performance_alert(model_name, "high_p95_latency", p95_latency)

    async def _anomaly_detection_loop(self):
        """Background loop for detecting anomalies in stream processing."""
        while self.running:
            try:
                await asyncio.sleep(180)  # Check every 3 minutes
                
                await self._detect_processing_anomalies()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in anomaly detection loop: {e}")

    async def _detect_processing_anomalies(self):
        """Detects anomalies in processing patterns."""
        if not self.metrics_buffer:
            return
        
        # Get recent metrics (last 10 minutes)
        cutoff_time = datetime.utcnow() - timedelta(minutes=10)
        recent_metrics = [
            m for m in self.metrics_buffer
            if datetime.fromisoformat(m["timestamp"]) > cutoff_time
        ]
        
        if len(recent_metrics) < 10:  # Need minimum data for anomaly detection
            return
        
        # Detect throughput anomalies
        throughput_by_minute = {}
        for metric in recent_metrics:
            minute = datetime.fromisoformat(metric["timestamp"]).strftime("%Y-%m-%d %H:%M")
            throughput_by_minute[minute] = throughput_by_minute.get(minute, 0) + 1
        
        if throughput_by_minute:
            throughput_values = list(throughput_by_minute.values())
            mean_throughput = np.mean(throughput_values)
            std_throughput = np.std(throughput_values)
            
            # Detect significant deviations
            for minute, throughput in throughput_by_minute.items():
                if std_throughput > 0 and abs(throughput - mean_throughput) > 2 * std_throughput:
                    logger.warning(f"Throughput anomaly detected at {minute}: {throughput} events")
                    await self._trigger_anomaly_alert("throughput_anomaly", {
                        "minute": minute,
                        "throughput": throughput,
                        "mean_throughput": mean_throughput,
                        "std_throughput": std_throughput
                    })

    async def _trigger_performance_alert(self, model_name: str, alert_type: str, value: float):
        """Triggers a performance alert."""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": "performance",
            "model_name": model_name,
            "alert_subtype": alert_type,
            "value": value,
            "threshold": SETTINGS.performance_degradation_threshold
        }
        
        logger.warning(f"Performance alert: {alert}")
        
        # Update alert counts
        alert_key = f"{model_name}_{alert_type}"
        self.alert_counts[alert_key] = self.alert_counts.get(alert_key, 0) + 1

    async def _trigger_anomaly_alert(self, alert_type: str, metadata: Dict[str, Any]):
        """Triggers an anomaly alert."""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": "anomaly",
            "alert_subtype": alert_type,
            "metadata": metadata
        }
        
        logger.warning(f"Anomaly alert: {alert}")
        
        # Update alert counts
        self.alert_counts[alert_type] = self.alert_counts.get(alert_type, 0) + 1

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Gets a summary of current analytics."""
        current_time = datetime.utcnow()
        
        # Calculate recent metrics (last hour)
        cutoff_time = current_time - timedelta(hours=1)
        recent_metrics = [
            m for m in self.metrics_buffer
            if datetime.fromisoformat(m["timestamp"]) > cutoff_time
        ]
        
        # Calculate summary statistics
        total_events = len(recent_metrics)
        successful_events = sum(1 for m in recent_metrics if m["success"])
        error_events = total_events - successful_events
        
        # Calculate model performance
        model_performance = {}
        for model_name, processing_times in self.performance_metrics.items():
            if processing_times:
                model_performance[model_name] = {
                    "avg_latency": round(np.mean(processing_times), 3),
                    "p95_latency": round(np.percentile(processing_times, 95), 3),
                    "p99_latency": round(np.percentile(processing_times, 99), 3),
                    "total_predictions": len(processing_times)
                }
        
        # Calculate throughput by event type
        throughput_summary = {}
        for event_type, counts in self.throughput_metrics.items():
            if counts:
                throughput_summary[event_type] = {
                    "events_per_minute": round(np.mean(counts), 2),
                    "total_events": sum(counts)
                }
        
        return {
            "timestamp": current_time.isoformat(),
            "summary": {
                "total_events": total_events,
                "successful_events": successful_events,
                "error_events": error_events,
                "success_rate": round(successful_events / total_events, 3) if total_events > 0 else 0,
                "avg_processing_time": round(np.mean([m["processing_time"] for m in recent_metrics]), 3) if recent_metrics else 0
            },
            "model_performance": model_performance,
            "throughput": throughput_summary,
            "alert_counts": self.alert_counts,
            "buffer_size": len(self.metrics_buffer)
        }

    async def get_model_performance(self, model_name: str) -> Dict[str, Any]:
        """Gets performance metrics for a specific model."""
        if model_name not in self.performance_metrics:
            return {"error": f"No performance data for model {model_name}"}
        
        processing_times = self.performance_metrics[model_name]
        
        if not processing_times:
            return {"error": f"No processing times recorded for model {model_name}"}
        
        return {
            "model_name": model_name,
            "total_predictions": len(processing_times),
            "avg_latency": round(np.mean(processing_times), 3),
            "median_latency": round(np.median(processing_times), 3),
            "p95_latency": round(np.percentile(processing_times, 95), 3),
            "p99_latency": round(np.percentile(processing_times, 99), 3),
            "min_latency": round(np.min(processing_times), 3),
            "max_latency": round(np.max(processing_times), 3),
            "std_latency": round(np.std(processing_times), 3)
        }

    async def reset_metrics(self):
        """Resets all analytics metrics."""
        self.metrics_buffer.clear()
        self.alert_counts.clear()
        self.performance_metrics.clear()
        self.throughput_metrics.clear()
        logger.info("Analytics metrics reset")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.create_task(self.stop_analytics())
