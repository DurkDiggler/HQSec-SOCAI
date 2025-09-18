"""Apache Kafka consumer for real-time event processing."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from ..config import SETTINGS

logger = logging.getLogger(__name__)

class KafkaEventConsumer:
    """
    Kafka consumer for processing real-time security events and ML predictions.
    """

    def __init__(self, bootstrap_servers: str = None, topic_prefix: str = "soc-agent"):
        self.bootstrap_servers = bootstrap_servers or SETTINGS.kafka_bootstrap_servers
        self.topic_prefix = topic_prefix
        self.consumer = None
        self.running = False
        self._message_handlers: Dict[str, Callable] = {}

    def _connect(self, topics: List[str], group_id: str = "soc-agent-consumer"):
        """Establishes connection to Kafka cluster and subscribes to topics."""
        try:
            self.consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                max_poll_records=100,
                max_poll_interval_ms=300000
            )
            logger.info(f"Connected to Kafka cluster at {self.bootstrap_servers}, subscribed to topics: {topics}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def register_handler(self, topic_suffix: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Registers a message handler for a specific topic.
        
        Args:
            topic_suffix: Topic suffix (e.g., 'events', 'ml-predictions')
            handler: Async function to handle messages
        """
        topic = f"{self.topic_prefix}-{topic_suffix}"
        self._message_handlers[topic] = handler
        logger.info(f"Registered handler for topic: {topic}")

    async def start_consuming(self, topics: List[str], group_id: str = "soc-agent-consumer"):
        """
        Starts consuming messages from specified topics.
        
        Args:
            topics: List of topic suffixes to consume from
            group_id: Kafka consumer group ID
        """
        full_topics = [f"{self.topic_prefix}-{topic}" for topic in topics]
        self._connect(full_topics, group_id)
        self.running = True
        
        logger.info(f"Starting to consume from topics: {full_topics}")
        
        try:
            while self.running:
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    topic = topic_partition.topic
                    
                    for message in messages:
                        try:
                            # Get handler for this topic
                            handler = self._message_handlers.get(topic)
                            if handler:
                                await handler(message.value)
                            else:
                                logger.warning(f"No handler registered for topic: {topic}")
                                
                        except Exception as e:
                            logger.error(f"Error processing message from topic {topic}: {e}")
                            # Continue processing other messages
                            
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
        finally:
            self.stop_consuming()

    def stop_consuming(self):
        """Stops the consumer and closes the connection."""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer stopped and connection closed")

    async def consume_events(self, handler: Callable[[Dict[str, Any]], None]):
        """
        Convenience method to consume security events.
        
        Args:
            handler: Function to handle security events
        """
        self.register_handler("events", handler)
        await self.start_consuming(["events"])

    async def consume_ml_predictions(self, handler: Callable[[Dict[str, Any]], None]):
        """
        Convenience method to consume ML prediction requests.
        
        Args:
            handler: Function to handle ML prediction requests
        """
        self.register_handler("ml-predictions", handler)
        await self.start_consuming(["ml-predictions"])

    async def consume_ml_training(self, handler: Callable[[Dict[str, Any]], None]):
        """
        Convenience method to consume ML training data.
        
        Args:
            handler: Function to handle ML training data
        """
        self.register_handler("ml-training", handler)
        await self.start_consuming(["ml-training"])

    async def consume_ml_feedback(self, handler: Callable[[Dict[str, Any]], None]):
        """
        Convenience method to consume ML feedback data.
        
        Args:
            handler: Function to handle ML feedback
        """
        self.register_handler("ml-feedback", handler)
        await self.start_consuming(["ml-feedback"])

    async def consume_all_topics(self, handlers: Dict[str, Callable[[Dict[str, Any]], None]]):
        """
        Consumes from all topics with their respective handlers.
        
        Args:
            handlers: Dict mapping topic suffixes to handler functions
        """
        for topic_suffix, handler in handlers.items():
            self.register_handler(topic_suffix, handler)
        
        topics = list(handlers.keys())
        await self.start_consuming(topics)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_consuming()
