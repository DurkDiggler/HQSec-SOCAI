"""API endpoints for real-time AI processing and stream analytics."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .config import SETTINGS
from .database import get_db
from .streaming.kafka_producer import KafkaEventProducer
from .streaming.kafka_consumer import KafkaEventConsumer
from .streaming.flink_processor import FlinkStreamProcessor
from .streaming.stream_analytics import StreamAnalytics
from .serving.tensorflow_serving import TensorFlowModelServer
from .serving.mlflow_serving import MLflowModelServer
from .serving.ab_testing import ABTestingFramework
from .auto_retraining.retraining_scheduler import RetrainingScheduler
from .auto_retraining.retraining_pipeline import RetrainingPipeline
from .ml.model_manager import MLModelManager

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1/streaming", tags=["streaming"])

# Initialize components
ml_model_manager = MLModelManager()
kafka_producer = KafkaEventProducer()
kafka_consumer = KafkaEventConsumer()
flink_processor = FlinkStreamProcessor(ml_model_manager)
stream_analytics = StreamAnalytics()
tf_serving = TensorFlowModelServer()
mlflow_serving = MLflowModelServer()
ab_testing = ABTestingFramework()
retraining_scheduler = RetrainingScheduler(ml_model_manager)
retraining_pipeline = RetrainingPipeline(ml_model_manager)

@router.on_event("startup")
async def startup_event():
    """Initialize streaming components on startup."""
    logger.info("Initializing streaming components...")
    
    # Start stream analytics
    await stream_analytics.start_analytics()
    
    # Start retraining scheduler
    await retraining_scheduler.start_scheduler()
    
    logger.info("Streaming components initialized")

@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup streaming components on shutdown."""
    logger.info("Shutting down streaming components...")
    
    # Stop components
    await stream_analytics.stop_analytics()
    await retraining_scheduler.stop_scheduler()
    await flink_processor.stop_processing()
    
    # Close connections
    kafka_producer.close()
    kafka_consumer.stop_consuming()
    
    logger.info("Streaming components shut down")

# Stream Processing Endpoints

@router.post("/events", response_model=Dict[str, Any])
async def send_event(event_data: Dict[str, Any], topic_suffix: str = "events"):
    """Send a security event to the stream processing pipeline."""
    try:
        success = await kafka_producer.send_event(event_data, topic_suffix)
        if success:
            # Record analytics
            await stream_analytics.record_event(
                event_type="event_sent",
                processing_time=0.0,
                success=True
            )
            return {"status": "success", "message": "Event sent to stream"}
        else:
            return {"status": "error", "message": "Failed to send event"}
    except Exception as e:
        logger.error(f"Error sending event: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/events/batch", response_model=Dict[str, Any])
async def send_batch_events(events: List[Dict[str, Any]], topic_suffix: str = "events"):
    """Send multiple events to the stream processing pipeline."""
    try:
        results = await kafka_producer.send_batch_events(events, topic_suffix)
        
        # Record analytics
        await stream_analytics.record_event(
            event_type="batch_events_sent",
            processing_time=0.0,
            success=True,
            metadata={"event_count": len(events)}
        )
        
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Error sending batch events: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/ml/predict", response_model=Dict[str, Any])
async def request_ml_prediction(event_data: Dict[str, Any], model_type: str):
    """Request ML prediction for an event."""
    try:
        success = await kafka_producer.send_ml_prediction_request(event_data, model_type)
        if success:
            return {"status": "success", "message": "Prediction request sent"}
        else:
            return {"status": "error", "message": "Failed to send prediction request"}
    except Exception as e:
        logger.error(f"Error requesting ML prediction: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/ml/train", response_model=Dict[str, Any])
async def request_ml_training(training_data: List[Dict[str, Any]], model_type: str):
    """Request ML model training with new data."""
    try:
        success = await kafka_producer.send_model_training_data(training_data, model_type)
        if success:
            return {"status": "success", "message": "Training request sent"}
        else:
            return {"status": "error", "message": "Failed to send training request"}
    except Exception as e:
        logger.error(f"Error requesting ML training: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/ml/feedback", response_model=Dict[str, Any])
async def send_ml_feedback(event_id: str, feedback: Dict[str, Any], model_type: str):
    """Send feedback for ML model improvement."""
    try:
        success = await kafka_producer.send_model_feedback(event_id, feedback, model_type)
        if success:
            return {"status": "success", "message": "Feedback sent"}
        else:
            return {"status": "error", "message": "Failed to send feedback"}
    except Exception as e:
        logger.error(f"Error sending ML feedback: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Stream Analytics Endpoints

@router.get("/analytics/summary", response_model=Dict[str, Any])
async def get_analytics_summary():
    """Get real-time analytics summary."""
    try:
        summary = await stream_analytics.get_analytics_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics/model/{model_name}", response_model=Dict[str, Any])
async def get_model_performance(model_name: str):
    """Get performance metrics for a specific model."""
    try:
        performance = await stream_analytics.get_model_performance(model_name)
        return performance
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/analytics/reset", response_model=Dict[str, Any])
async def reset_analytics():
    """Reset analytics metrics."""
    try:
        await stream_analytics.reset_metrics()
        return {"status": "success", "message": "Analytics metrics reset"}
    except Exception as e:
        logger.error(f"Error resetting analytics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Model Serving Endpoints

@router.post("/serving/tf/predict", response_model=Dict[str, Any])
async def tf_serving_predict(model_name: str, inputs: Dict[str, Any], version: str = None):
    """Make prediction using TensorFlow Serving."""
    try:
        if not await tf_serving.health_check():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="TensorFlow Serving not available")
        
        result = await tf_serving.predict(model_name, inputs, version)
        return result
    except Exception as e:
        logger.error(f"Error with TensorFlow Serving prediction: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/serving/mlflow/predict", response_model=Dict[str, Any])
async def mlflow_serving_predict(model_name: str, inputs: Dict[str, Any], version: str = "latest"):
    """Make prediction using MLflow serving."""
    try:
        if not await mlflow_serving.health_check():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MLflow serving not available")
        
        result = await mlflow_serving.predict(model_name, inputs, version)
        return result
    except Exception as e:
        logger.error(f"Error with MLflow serving prediction: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/serving/tf/status", response_model=Dict[str, Any])
async def get_tf_serving_status():
    """Get TensorFlow Serving status."""
    try:
        status = await tf_serving.get_model_status()
        return status
    except Exception as e:
        logger.error(f"Error getting TensorFlow Serving status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/serving/mlflow/status", response_model=Dict[str, Any])
async def get_mlflow_serving_status():
    """Get MLflow serving status."""
    try:
        # This would return MLflow serving status
        return {"status": "running", "message": "MLflow serving is operational"}
    except Exception as e:
        logger.error(f"Error getting MLflow serving status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# A/B Testing Endpoints

@router.post("/ab-testing/create", response_model=Dict[str, Any])
async def create_ab_test(
    test_name: str,
    model_a: str,
    model_b: str,
    traffic_split: float = 0.5,
    success_metric: str = "accuracy"
):
    """Create a new A/B test."""
    try:
        test_id = await ab_testing.create_ab_test(
            test_name=test_name,
            model_a=model_a,
            model_b=model_b,
            traffic_split=traffic_split,
            success_metric=success_metric
        )
        return {"test_id": test_id, "status": "created"}
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/ab-testing/{test_id}/assign", response_model=Dict[str, Any])
async def assign_model_variant(test_id: str, user_id: str = None):
    """Assign a model variant for A/B testing."""
    try:
        model = await ab_testing.assign_model(test_id, user_id)
        return {"assigned_model": model, "test_id": test_id}
    except Exception as e:
        logger.error(f"Error assigning model variant: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/ab-testing/{test_id}/record", response_model=Dict[str, Any])
async def record_ab_test_result(
    test_id: str,
    model_name: str,
    prediction: Any,
    ground_truth: Any,
    metadata: Dict[str, Any] = None
):
    """Record a result for A/B testing."""
    try:
        success = await ab_testing.record_result(
            test_id=test_id,
            model_name=model_name,
            prediction=prediction,
            ground_truth=ground_truth,
            metadata=metadata
        )
        return {"status": "success" if success else "error"}
    except Exception as e:
        logger.error(f"Error recording A/B test result: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/ab-testing/{test_id}/analyze", response_model=Dict[str, Any])
async def analyze_ab_test(test_id: str):
    """Analyze A/B test results."""
    try:
        analysis = await ab_testing.analyze_test(test_id)
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing A/B test: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/ab-testing", response_model=List[Dict[str, Any]])
async def get_all_ab_tests():
    """Get all A/B tests."""
    try:
        tests = await ab_testing.get_all_tests()
        return tests
    except Exception as e:
        logger.error(f"Error getting A/B tests: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Auto-Retraining Endpoints

@router.get("/retraining/status", response_model=Dict[str, Any])
async def get_retraining_status():
    """Get retraining scheduler status."""
    try:
        status = await retraining_scheduler.get_retraining_status()
        return status
    except Exception as e:
        logger.error(f"Error getting retraining status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/retraining/force", response_model=Dict[str, Any])
async def force_retraining(reason: str = "Manual trigger"):
    """Force a retraining pipeline run."""
    try:
        success = await retraining_scheduler.force_retraining(reason)
        return {"status": "success" if success else "error", "reason": reason}
    except Exception as e:
        logger.error(f"Error forcing retraining: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/retraining/pipeline/run", response_model=Dict[str, Any])
async def run_retraining_pipeline(
    trigger_reason: str = "manual",
    data_types: List[str] = None,
    models_to_retrain: List[str] = None
):
    """Run the complete retraining pipeline."""
    try:
        result = await retraining_pipeline.run_full_pipeline(
            trigger_reason=trigger_reason,
            data_types=data_types,
            models_to_retrain=models_to_retrain
        )
        return result
    except Exception as e:
        logger.error(f"Error running retraining pipeline: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/retraining/history", response_model=List[Dict[str, Any]])
async def get_retraining_history(limit: int = 10):
    """Get retraining history."""
    try:
        history = await retraining_scheduler.get_retraining_history(limit)
        return history
    except Exception as e:
        logger.error(f"Error getting retraining history: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Health Check

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check for streaming components."""
    try:
        health_status = {
            "kafka_producer": True,  # Simplified - would check actual connection
            "kafka_consumer": True,
            "flink_processor": flink_processor.running,
            "stream_analytics": stream_analytics.running,
            "tf_serving": await tf_serving.health_check(),
            "mlflow_serving": await mlflow_serving.health_check(),
            "retraining_scheduler": retraining_scheduler.running
        }
        
        overall_health = all(health_status.values())
        
        return {
            "status": "healthy" if overall_health else "degraded",
            "components": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
