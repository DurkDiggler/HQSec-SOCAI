"""Retraining scheduler for continuous model improvement."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..config import SETTINGS
from ..ml.model_manager import MLModelManager
from .data_collector import DataCollector
from .model_validator import ModelValidator

logger = logging.getLogger(__name__)

class RetrainingScheduler:
    """
    Schedules and manages automatic model retraining based on various triggers.
    Supports time-based, performance-based, and data drift-based retraining.
    """

    def __init__(self, model_manager: MLModelManager = None):
        self.model_manager = model_manager or MLModelManager()
        self.data_collector = DataCollector()
        self.model_validator = ModelValidator()
        self.running = False
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}
        self.retraining_history: List[Dict[str, Any]] = []

    async def start_scheduler(self):
        """Starts the retraining scheduler."""
        if self.running:
            logger.warning("Retraining scheduler is already running")
            return
        
        self.running = True
        logger.info("Starting retraining scheduler...")
        
        # Start different types of retraining tasks
        if SETTINGS.auto_retrain_enabled:
            # Time-based retraining
            if SETTINGS.retrain_interval_hours > 0:
                self.scheduled_tasks["time_based"] = asyncio.create_task(
                    self._time_based_retraining_loop()
                )
            
            # Performance-based retraining
            if SETTINGS.performance_based_retraining:
                self.scheduled_tasks["performance_based"] = asyncio.create_task(
                    self._performance_based_retraining_loop()
                )
            
            # Data drift-based retraining
            if SETTINGS.drift_based_retraining:
                self.scheduled_tasks["drift_based"] = asyncio.create_task(
                    self._drift_based_retraining_loop()
                )
            
            # Feedback-based retraining
            if SETTINGS.feedback_based_retraining:
                self.scheduled_tasks["feedback_based"] = asyncio.create_task(
                    self._feedback_based_retraining_loop()
                )
        
        logger.info("Retraining scheduler started successfully")

    async def stop_scheduler(self):
        """Stops the retraining scheduler."""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping retraining scheduler...")
        
        # Cancel all scheduled tasks
        for task_name, task in self.scheduled_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled {task_name} retraining task")
        
        self.scheduled_tasks.clear()
        logger.info("Retraining scheduler stopped")

    async def _time_based_retraining_loop(self):
        """Time-based retraining loop."""
        while self.running:
            try:
                await asyncio.sleep(SETTINGS.retrain_interval_hours * 3600)  # Convert hours to seconds
                
                if self.running:  # Check again after sleep
                    logger.info("Triggering time-based retraining...")
                    await self._trigger_retraining("time_based", "Scheduled time-based retraining")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in time-based retraining loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying

    async def _performance_based_retraining_loop(self):
        """Performance-based retraining loop."""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Check every hour
                
                if self.running:
                    # Check model performance
                    performance_degraded = await self._check_performance_degradation()
                    
                    if performance_degraded:
                        logger.warning("Performance degradation detected, triggering retraining...")
                        await self._trigger_retraining("performance_based", "Performance degradation detected")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance-based retraining loop: {e}")
                await asyncio.sleep(3600)

    async def _drift_based_retraining_loop(self):
        """Data drift-based retraining loop."""
        while self.running:
            try:
                await asyncio.sleep(1800)  # Check every 30 minutes
                
                if self.running:
                    # Check for data drift
                    drift_detected = await self._check_data_drift()
                    
                    if drift_detected:
                        logger.warning("Data drift detected, triggering retraining...")
                        await self._trigger_retraining("drift_based", "Data drift detected")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in drift-based retraining loop: {e}")
                await asyncio.sleep(1800)

    async def _feedback_based_retraining_loop(self):
        """Feedback-based retraining loop."""
        while self.running:
            try:
                await asyncio.sleep(7200)  # Check every 2 hours
                
                if self.running:
                    # Check for sufficient new feedback
                    feedback_available = await self._check_feedback_availability()
                    
                    if feedback_available:
                        logger.info("Sufficient feedback available, triggering retraining...")
                        await self._trigger_retraining("feedback_based", "Sufficient feedback available")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in feedback-based retraining loop: {e}")
                await asyncio.sleep(7200)

    async def _check_performance_degradation(self) -> bool:
        """Checks if model performance has degraded below threshold."""
        try:
            # Get current model performance metrics
            performance_metrics = await self.model_validator.get_current_performance()
            
            for model_name, metrics in performance_metrics.items():
                current_accuracy = metrics.get("accuracy", 0)
                threshold = SETTINGS.performance_degradation_threshold
                
                if current_accuracy < threshold:
                    logger.warning(f"Model {model_name} performance degraded: {current_accuracy:.3f} < {threshold}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking performance degradation: {e}")
            return False

    async def _check_data_drift(self) -> bool:
        """Checks if significant data drift has been detected."""
        try:
            # This would integrate with the model monitor's drift detection
            # For now, we'll use a simple heuristic
            drift_status = await self.model_manager.ml_model_monitor.get_drift_status()
            
            for model_name, status in drift_status.items():
                if status.get("drift_detected", False):
                    logger.warning(f"Data drift detected for model {model_name}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking data drift: {e}")
            return False

    async def _check_feedback_availability(self) -> bool:
        """Checks if sufficient new feedback is available for retraining."""
        try:
            # Check if we have enough new feedback since last retraining
            feedback_count = await self.data_collector.get_feedback_count_since_last_retraining()
            required_feedback = SETTINGS.min_feedback_for_retraining
            
            if feedback_count >= required_feedback:
                logger.info(f"Sufficient feedback available: {feedback_count} >= {required_feedback}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking feedback availability: {e}")
            return False

    async def _trigger_retraining(self, trigger_type: str, reason: str):
        """Triggers model retraining."""
        try:
            logger.info(f"Starting retraining triggered by {trigger_type}: {reason}")
            
            # Collect new training data
            training_data = await self.data_collector.collect_training_data()
            
            if not training_data:
                logger.warning("No training data available for retraining")
                return
            
            # Validate data quality
            data_quality = await self.model_validator.validate_data_quality(training_data)
            if not data_quality["is_valid"]:
                logger.warning(f"Training data quality insufficient: {data_quality['issues']}")
                return
            
            # Perform retraining
            retraining_start = datetime.utcnow()
            
            # Retrain all models
            await self.model_manager.retrain_all_models(force_retrain=True)
            
            retraining_end = datetime.utcnow()
            duration = (retraining_end - retraining_start).total_seconds()
            
            # Validate new models
            validation_results = await self.model_validator.validate_models()
            
            # Record retraining history
            retraining_record = {
                "trigger_type": trigger_type,
                "reason": reason,
                "start_time": retraining_start.isoformat(),
                "end_time": retraining_end.isoformat(),
                "duration_seconds": duration,
                "training_data_size": len(training_data),
                "validation_results": validation_results,
                "success": all(r.get("is_valid", False) for r in validation_results.values())
            }
            
            self.retraining_history.append(retraining_record)
            
            # Keep only last N retraining records
            max_history = 100
            if len(self.retraining_history) > max_history:
                self.retraining_history = self.retraining_history[-max_history:]
            
            if retraining_record["success"]:
                logger.info(f"Retraining completed successfully in {duration:.2f} seconds")
            else:
                logger.error("Retraining completed but validation failed")
            
        except Exception as e:
            logger.error(f"Error during retraining: {e}")
            
            # Record failed retraining
            retraining_record = {
                "trigger_type": trigger_type,
                "reason": reason,
                "start_time": datetime.utcnow().isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "duration_seconds": 0,
                "training_data_size": 0,
                "validation_results": {},
                "success": False,
                "error": str(e)
            }
            self.retraining_history.append(retraining_record)

    async def get_retraining_status(self) -> Dict[str, Any]:
        """Gets the current status of the retraining scheduler."""
        return {
            "running": self.running,
            "active_tasks": list(self.scheduled_tasks.keys()),
            "retraining_history_count": len(self.retraining_history),
            "last_retraining": self.retraining_history[-1] if self.retraining_history else None,
            "settings": {
                "auto_retrain_enabled": SETTINGS.auto_retrain_enabled,
                "retrain_interval_hours": SETTINGS.retrain_interval_hours,
                "performance_based_retraining": SETTINGS.performance_based_retraining,
                "drift_based_retraining": SETTINGS.drift_based_retraining,
                "feedback_based_retraining": SETTINGS.feedback_based_retraining
            }
        }

    async def get_retraining_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Gets the retraining history."""
        return self.retraining_history[-limit:] if self.retraining_history else []

    async def force_retraining(self, reason: str = "Manual trigger") -> bool:
        """Manually triggers retraining."""
        try:
            await self._trigger_retraining("manual", reason)
            return True
        except Exception as e:
            logger.error(f"Error in manual retraining: {e}")
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.create_task(self.stop_scheduler())
