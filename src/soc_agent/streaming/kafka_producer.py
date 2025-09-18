"""Apache Kafka producer for real-time event streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from kafka import KafkaProducer
from kafka.errors import KafkaError

from ..config import SETTINGS

logger = logging.getLogger(__name__)

class KafkaEventProducer:
    """
    Kafka producer for streaming security events to real-time AI processing pipeline.
    """

    def __init__(self, bootstrap_servers: str = None, topic_prefix: str = "soc-agent"):
        self.bootstrap_servers = bootstrap_servers or SETTINGS.kafka_bootstrap_servers
        self.topic_prefix = topic_prefix
        self.producer = None
        self._connect()

    def _connect(self):
        """Establishes connection to Kafka cluster."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                retry_backoff_ms=100,
                request_timeout_ms=30000,
                max_block_ms=10000
            )
            logger.info(f"Connected to Kafka cluster at {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    async def send_event(self, event: Dict[str, Any], topic_suffix: str = "events") -> bool:
        """
        Sends a single security event to Kafka topic.
        
        Args:
            event: Security event data
            topic_suffix: Topic suffix (e.g., 'events', 'alerts', 'incidents')
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.producer:
            logger.error("Kafka producer not connected")
            return False

        topic = f"{self.topic_prefix}-{topic_suffix}"
        
        # Add metadata to event
        enriched_event = {
            **event,
            "timestamp": datetime.utcnow().isoformat(),
            "producer_id": "soc-agent-producer",
            "event_id": event.get("id", f"event_{datetime.utcnow().timestamp()}")
        }

        try:
            # Send event asynchronously
            future = self.producer.send(
                topic,
                value=enriched_event,
                key=enriched_event["event_id"]
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            logger.debug(f"Event sent to topic {record_metadata.topic}, partition {record_metadata.partition}, offset {record_metadata.offset}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send event to Kafka: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending event: {e}")
            return False

    async def send_batch_events(self, events: List[Dict[str, Any]], topic_suffix: str = "events") -> Dict[str, int]:
        """
        Sends multiple events in batch for better throughput.
        
        Args:
            events: List of security events
            topic_suffix: Topic suffix
            
        Returns:
            Dict with success/failure counts
        """
        if not self.producer:
            logger.error("Kafka producer not connected")
            return {"success": 0, "failed": len(events)}

        topic = f"{self.topic_prefix}-{topic_suffix}"
        results = {"success": 0, "failed": 0}
        
        futures = []
        
        for event in events:
            enriched_event = {
                **event,
                "timestamp": datetime.utcnow().isoformat(),
                "producer_id": "soc-agent-producer",
                "event_id": event.get("id", f"event_{datetime.utcnow().timestamp()}")
            }
            
            try:
                future = self.producer.send(
                    topic,
                    value=enriched_event,
                    key=enriched_event["event_id"]
                )
                futures.append((future, event))
            except Exception as e:
                logger.error(f"Failed to queue event for sending: {e}")
                results["failed"] += 1

        # Wait for all futures to complete
        for future, event in futures:
            try:
                record_metadata = future.get(timeout=10)
                results["success"] += 1
                logger.debug(f"Batch event sent to topic {record_metadata.topic}")
            except Exception as e:
                logger.error(f"Failed to send batch event: {e}")
                results["failed"] += 1

        logger.info(f"Batch send completed: {results['success']} success, {results['failed']} failed")
        return results

    async def send_ml_prediction_request(self, event: Dict[str, Any], model_type: str) -> bool:
        """
        Sends event to ML prediction topic for real-time analysis.
        
        Args:
            event: Event data for ML analysis
            model_type: Type of ML model (anomaly, risk, classification, etc.)
        """
        ml_event = {
            **event,
            "ml_model_type": model_type,
            "prediction_request": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.send_event(ml_event, "ml-predictions")

    async def send_model_training_data(self, training_data: List[Dict[str, Any]], model_type: str) -> bool:
        """
        Sends training data to model training topic.
        
        Args:
            training_data: Training data for ML models
            model_type: Type of ML model to train
        """
        training_event = {
            "model_type": model_type,
            "training_data": training_data,
            "data_count": len(training_data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.send_event(training_event, "ml-training")

    async def send_model_feedback(self, event_id: str, feedback: Dict[str, Any], model_type: str) -> bool:
        """
        Sends model prediction feedback for continuous learning.
        
        Args:
            event_id: ID of the original event
            feedback: Feedback data (correctness, corrections, etc.)
            model_type: Type of ML model
        """
        feedback_event = {
            "original_event_id": event_id,
            "model_type": model_type,
            "feedback": feedback,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.send_event(feedback_event, "ml-feedback")

    def close(self):
        """Closes the Kafka producer connection."""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
