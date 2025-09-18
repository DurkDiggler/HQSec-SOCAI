"""Apache Flink stream processor for real-time AI analysis."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..config import SETTINGS
from ..ml.model_manager import MLModelManager
from ..streaming.kafka_consumer import KafkaEventConsumer
from ..streaming.kafka_producer import KafkaEventProducer

logger = logging.getLogger(__name__)

class FlinkStreamProcessor:
    """
    Apache Flink-based stream processor for real-time AI analysis.
    Handles complex event processing, windowing, and ML inference.
    """

    def __init__(self, model_manager: MLModelManager = None):
        self.model_manager = model_manager or MLModelManager()
        self.kafka_consumer = KafkaEventConsumer()
        self.kafka_producer = KafkaEventProducer()
        self.running = False
        self._event_windows: Dict[str, List[Dict[str, Any]]] = {}
        self._processing_stats = {
            "events_processed": 0,
            "ml_predictions": 0,
            "anomalies_detected": 0,
            "campaigns_detected": 0,
            "errors": 0
        }

    async def start_processing(self):
        """Starts the Flink stream processing pipeline."""
        logger.info("Starting Flink stream processor...")
        self.running = True
        
        # Register handlers for different event types
        handlers = {
            "events": self._process_security_event,
            "ml-predictions": self._process_ml_prediction_request,
            "ml-training": self._process_ml_training_data,
            "ml-feedback": self._process_ml_feedback
        }
        
        # Start consuming from all topics
        await self.kafka_consumer.consume_all_topics(handlers)

    async def _process_security_event(self, event: Dict[str, Any]):
        """
        Processes a single security event through the AI pipeline.
        
        Args:
            event: Security event data
        """
        try:
            self._processing_stats["events_processed"] += 1
            
            # Add to event window for pattern analysis
            await self._add_to_event_window(event)
            
            # Run real-time ML analysis
            await self._run_realtime_analysis(event)
            
            # Check for campaign patterns
            await self._check_campaign_patterns(event)
            
            logger.debug(f"Processed security event: {event.get('id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error processing security event: {e}")
            self._processing_stats["errors"] += 1

    async def _process_ml_prediction_request(self, event: Dict[str, Any]):
        """
        Processes ML prediction requests.
        
        Args:
            event: ML prediction request data
        """
        try:
            model_type = event.get("ml_model_type")
            if not model_type:
                logger.warning("ML prediction request missing model type")
                return
            
            # Run ML inference
            result = await self.model_manager.run_inference(model_type, event)
            
            # Send prediction result back
            prediction_result = {
                "original_event_id": event.get("event_id"),
                "model_type": model_type,
                "prediction": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.kafka_producer.send_event(prediction_result, "ml-results")
            self._processing_stats["ml_predictions"] += 1
            
        except Exception as e:
            logger.error(f"Error processing ML prediction request: {e}")
            self._processing_stats["errors"] += 1

    async def _process_ml_training_data(self, event: Dict[str, Any]):
        """
        Processes ML training data for model updates.
        
        Args:
            event: ML training data
        """
        try:
            model_type = event.get("model_type")
            training_data = event.get("training_data", [])
            
            if not model_type or not training_data:
                logger.warning("ML training data missing model type or training data")
                return
            
            logger.info(f"Processing training data for {model_type}: {len(training_data)} samples")
            
            # Trigger model retraining
            if model_type == "anomaly_detector":
                await self.model_manager.anomaly_detector.train_model(training_data)
            elif model_type == "risk_scorer":
                await self.model_manager.risk_scorer.train_model(training_data)
            elif model_type == "incident_classifier":
                await self.model_manager.incident_classifier.train_model(training_data)
            elif model_type == "false_positive_filter":
                await self.model_manager.false_positive_filter.train_model(training_data)
            elif model_type == "pattern_recognizer":
                alert_messages = [d.get("message", "") for d in training_data if d.get("message")]
                if alert_messages:
                    await self.model_manager.pattern_recognizer.train_vectorizer(alert_messages)
            
            logger.info(f"Model {model_type} retrained successfully")
            
        except Exception as e:
            logger.error(f"Error processing ML training data: {e}")
            self._processing_stats["errors"] += 1

    async def _process_ml_feedback(self, event: Dict[str, Any]):
        """
        Processes ML model feedback for continuous learning.
        
        Args:
            event: ML feedback data
        """
        try:
            original_event_id = event.get("original_event_id")
            model_type = event.get("model_type")
            feedback = event.get("feedback", {})
            
            if not all([original_event_id, model_type, feedback]):
                logger.warning("ML feedback missing required fields")
                return
            
            # Store feedback for model improvement
            # This could trigger incremental learning or model updates
            logger.info(f"Received feedback for {model_type} model: {feedback}")
            
            # Send feedback to model training pipeline
            feedback_event = {
                "model_type": model_type,
                "feedback_data": feedback,
                "original_event_id": original_event_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.kafka_producer.send_event(feedback_event, "ml-training")
            
        except Exception as e:
            logger.error(f"Error processing ML feedback: {e}")
            self._processing_stats["errors"] += 1

    async def _add_to_event_window(self, event: Dict[str, Any]):
        """
        Adds event to sliding window for pattern analysis.
        
        Args:
            event: Security event data
        """
        window_key = "security_events"
        if window_key not in self._event_windows:
            self._event_windows[window_key] = []
        
        # Add event to window
        self._event_windows[window_key].append(event)
        
        # Maintain window size (keep last N events)
        max_window_size = SETTINGS.stream_window_size
        if len(self._event_windows[window_key]) > max_window_size:
            self._event_windows[window_key] = self._event_windows[window_key][-max_window_size:]
        
        # Clean old events (older than window duration)
        cutoff_time = datetime.utcnow() - timedelta(minutes=SETTINGS.stream_window_duration_minutes)
        self._event_windows[window_key] = [
            e for e in self._event_windows[window_key]
            if datetime.fromisoformat(e.get("timestamp", "1970-01-01T00:00:00")) > cutoff_time
        ]

    async def _run_realtime_analysis(self, event: Dict[str, Any]):
        """
        Runs real-time ML analysis on the event.
        
        Args:
            event: Security event data
        """
        try:
            # Anomaly detection
            if SETTINGS.anomaly_detection_enabled:
                anomaly_result = await self.model_manager.run_inference("anomaly_detector", event)
                if anomaly_result.get("is_anomaly", False):
                    self._processing_stats["anomalies_detected"] += 1
                    logger.warning(f"Anomaly detected: {anomaly_result}")
                    
                    # Send anomaly alert
                    await self.kafka_producer.send_event(anomaly_result, "anomaly-alerts")
            
            # Risk scoring
            if SETTINGS.risk_scoring_enabled:
                risk_result = await self.model_manager.run_inference("risk_scorer", event)
                if risk_result.get("risk_level") in ["HIGH", "CRITICAL"]:
                    logger.warning(f"High risk event: {risk_result}")
                    
                    # Send high-risk alert
                    await self.kafka_producer.send_event(risk_result, "risk-alerts")
            
            # Incident classification
            if SETTINGS.classification_enabled:
                classification_result = await self.model_manager.run_inference("incident_classifier", event)
                if classification_result.get("auto_classified", False):
                    logger.info(f"Auto-classified incident: {classification_result}")
                    
                    # Send classification result
                    await self.kafka_producer.send_event(classification_result, "incident-classifications")
            
            # False positive filtering
            if SETTINGS.fp_reduction_enabled:
                fp_result = await self.model_manager.run_inference("false_positive_filter", event)
                if fp_result.get("filtered", False):
                    logger.info(f"Filtered false positive: {fp_result}")
                    
                    # Send filtered alert
                    await self.kafka_producer.send_event(fp_result, "filtered-alerts")
            
        except Exception as e:
            logger.error(f"Error in real-time analysis: {e}")
            self._processing_stats["errors"] += 1

    async def _check_campaign_patterns(self, event: Dict[str, Any]):
        """
        Checks for attack campaign patterns using sliding window.
        
        Args:
            event: Security event data
        """
        try:
            if not SETTINGS.pattern_recognition_enabled:
                return
            
            window_key = "security_events"
            recent_events = self._event_windows.get(window_key, [])
            
            # Only check for campaigns if we have enough events
            if len(recent_events) >= SETTINGS.anomaly_min_samples:
                campaign_result = await self.model_manager.pattern_recognizer.recognize_patterns_and_campaigns(recent_events)
                
                campaigns = campaign_result.get("campaigns_detected", [])
                if campaigns:
                    self._processing_stats["campaigns_detected"] += len(campaigns)
                    logger.warning(f"Detected {len(campaigns)} attack campaigns")
                    
                    # Send campaign alerts
                    for campaign in campaigns:
                        await self.kafka_producer.send_event(campaign, "campaign-alerts")
        
        except Exception as e:
            logger.error(f"Error checking campaign patterns: {e}")
            self._processing_stats["errors"] += 1

    async def get_processing_stats(self) -> Dict[str, Any]:
        """Returns current processing statistics."""
        return {
            **self._processing_stats,
            "window_sizes": {k: len(v) for k, v in self._event_windows.items()},
            "running": self.running,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def stop_processing(self):
        """Stops the stream processing pipeline."""
        logger.info("Stopping Flink stream processor...")
        self.running = False
        self.kafka_consumer.stop_consuming()
        self.kafka_producer.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.create_task(self.stop_processing())
