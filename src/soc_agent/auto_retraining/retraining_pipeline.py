"""Complete retraining pipeline for continuous model improvement."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..config import SETTINGS
from ..ml.model_manager import MLModelManager
from ..serving.model_registry import ModelRegistry
from .data_collector import DataCollector
from .model_validator import ModelValidator

logger = logging.getLogger(__name__)

class RetrainingPipeline:
    """
    Complete retraining pipeline that orchestrates data collection,
    model training, validation, and deployment.
    """

    def __init__(self, model_manager: MLModelManager = None):
        self.model_manager = model_manager or MLModelManager()
        self.data_collector = DataCollector()
        self.model_validator = ModelValidator()
        self.model_registry = ModelRegistry()
        self.pipeline_stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run": None
        }

    async def run_full_pipeline(self, 
                               trigger_reason: str = "manual",
                               data_types: List[str] = None,
                               models_to_retrain: List[str] = None) -> Dict[str, Any]:
        """
        Runs the complete retraining pipeline.
        
        Args:
            trigger_reason: Reason for triggering retraining
            data_types: Types of data to collect
            models_to_retrain: Specific models to retrain (all if None)
            
        Returns:
            Dict containing pipeline execution results
        """
        pipeline_start = datetime.utcnow()
        self.pipeline_stats["total_runs"] += 1
        
        logger.info(f"Starting retraining pipeline: {trigger_reason}")
        
        try:
            # Step 1: Collect training data
            logger.info("Step 1: Collecting training data...")
            training_data = await self.data_collector.collect_training_data(data_types)
            
            if not training_data:
                raise Exception("No training data collected")
            
            # Step 2: Validate data quality
            logger.info("Step 2: Validating data quality...")
            data_quality = await self.data_collector.validate_data_quality(training_data)
            
            if not data_quality["is_valid"]:
                raise Exception(f"Data quality validation failed: {data_quality['issues']}")
            
            # Step 3: Preprocess data
            logger.info("Step 3: Preprocessing training data...")
            preprocessed_data = await self.data_collector.preprocess_training_data(training_data)
            
            # Step 4: Retrain models
            logger.info("Step 4: Retraining models...")
            retraining_results = await self._retrain_models(preprocessed_data, models_to_retrain)
            
            # Step 5: Validate new models
            logger.info("Step 5: Validating new models...")
            validation_results = await self.model_validator.validate_models()
            
            # Step 6: Register models if validation passes
            logger.info("Step 6: Registering models...")
            registration_results = await self._register_models(retraining_results, validation_results)
            
            # Step 7: Deploy models if registration successful
            logger.info("Step 7: Deploying models...")
            deployment_results = await self._deploy_models(registration_results)
            
            # Calculate pipeline metrics
            pipeline_end = datetime.utcnow()
            duration = (pipeline_end - pipeline_start).total_seconds()
            
            # Update pipeline stats
            self.pipeline_stats["successful_runs"] += 1
            self.pipeline_stats["last_run"] = {
                "timestamp": pipeline_start.isoformat(),
                "duration_seconds": duration,
                "trigger_reason": trigger_reason,
                "success": True
            }
            
            result = {
                "success": True,
                "pipeline_duration": duration,
                "data_collection": {
                    "total_data_points": sum(len(data) for data in training_data.values()),
                    "data_types": list(training_data.keys()),
                    "quality_score": data_quality
                },
                "retraining_results": retraining_results,
                "validation_results": validation_results,
                "registration_results": registration_results,
                "deployment_results": deployment_results,
                "timestamp": pipeline_start.isoformat()
            }
            
            logger.info(f"Retraining pipeline completed successfully in {duration:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Retraining pipeline failed: {e}")
            
            # Update pipeline stats
            self.pipeline_stats["failed_runs"] += 1
            pipeline_end = datetime.utcnow()
            duration = (pipeline_end - pipeline_start).total_seconds()
            
            self.pipeline_stats["last_run"] = {
                "timestamp": pipeline_start.isoformat(),
                "duration_seconds": duration,
                "trigger_reason": trigger_reason,
                "success": False,
                "error": str(e)
            }
            
            return {
                "success": False,
                "error": str(e),
                "pipeline_duration": duration,
                "timestamp": pipeline_start.isoformat()
            }

    async def _retrain_models(self, 
                             training_data: Dict[str, List[Dict[str, Any]]], 
                             models_to_retrain: List[str] = None) -> Dict[str, Any]:
        """Retrains specified models with new data."""
        retraining_results = {}
        
        # Define model retraining tasks
        retraining_tasks = {
            "anomaly_detector": {
                "data_key": "alerts",
                "retrain_func": self.model_manager.anomaly_detector.train_model
            },
            "risk_scorer": {
                "data_key": "risk_data",
                "retrain_func": self.model_manager.risk_scorer.train_model
            },
            "incident_classifier": {
                "data_key": "incidents",
                "retrain_func": self.model_manager.incident_classifier.train_model
            },
            "false_positive_filter": {
                "data_key": "feedback",
                "retrain_func": self.model_manager.false_positive_filter.train_model
            },
            "pattern_recognizer": {
                "data_key": "alerts",
                "retrain_func": self._retrain_pattern_recognizer
            }
        }
        
        # Filter models to retrain
        if models_to_retrain:
            retraining_tasks = {k: v for k, v in retraining_tasks.items() if k in models_to_retrain}
        
        # Retrain each model
        for model_name, task_info in retraining_tasks.items():
            try:
                data_key = task_info["data_key"]
                retrain_func = task_info["retrain_func"]
                
                if data_key not in training_data or not training_data[data_key]:
                    logger.warning(f"No training data available for {model_name}")
                    retraining_results[model_name] = {
                        "success": False,
                        "error": f"No training data available for {data_key}"
                    }
                    continue
                
                logger.info(f"Retraining {model_name} with {len(training_data[data_key])} samples...")
                
                # Retrain model
                await retrain_func(training_data[data_key])
                
                retraining_results[model_name] = {
                    "success": True,
                    "training_samples": len(training_data[data_key]),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info(f"Successfully retrained {model_name}")
                
            except Exception as e:
                logger.error(f"Failed to retrain {model_name}: {e}")
                retraining_results[model_name] = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return retraining_results

    async def _retrain_pattern_recognizer(self, training_data: List[Dict[str, Any]]):
        """Special retraining for pattern recognizer (needs alert messages)."""
        alert_messages = [d.get("message", "") for d in training_data if d.get("message")]
        if alert_messages:
            await self.model_manager.pattern_recognizer.train_vectorizer(alert_messages)
        else:
            raise Exception("No alert messages available for pattern recognizer training")

    async def _register_models(self, 
                              retraining_results: Dict[str, Any], 
                              validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Registers successfully retrained models."""
        registration_results = {}
        
        for model_name, retrain_result in retraining_results.items():
            if not retrain_result["success"]:
                registration_results[model_name] = {
                    "success": False,
                    "error": "Model retraining failed"
                }
                continue
            
            # Check validation results
            validation_result = validation_results.get(model_name, {})
            if not validation_result.get("is_valid", False):
                registration_results[model_name] = {
                    "success": False,
                    "error": "Model validation failed"
                }
                continue
            
            try:
                # Get the retrained model
                model_object = await self._get_retrained_model(model_name)
                if not model_object:
                    registration_results[model_name] = {
                        "success": False,
                        "error": "Could not retrieve retrained model"
                    }
                    continue
                
                # Register model
                version = await self.model_registry.register_model(
                    model_name=model_name,
                    model_object=model_object,
                    model_type="sklearn",
                    description=f"Auto-retrained {model_name}",
                    metrics=validation_result.get("metrics", {}),
                    tags={"auto_retrained": "true", "pipeline": "auto_retraining"}
                )
                
                registration_results[model_name] = {
                    "success": True,
                    "version": version,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info(f"Successfully registered {model_name} version {version}")
                
            except Exception as e:
                logger.error(f"Failed to register {model_name}: {e}")
                registration_results[model_name] = {
                    "success": False,
                    "error": str(e)
                }
        
        return registration_results

    async def _get_retrained_model(self, model_name: str) -> Optional[Any]:
        """Gets the retrained model object."""
        try:
            if model_name == "anomaly_detector":
                return self.model_manager.anomaly_detector.model
            elif model_name == "risk_scorer":
                return self.model_manager.risk_scorer.model
            elif model_name == "incident_classifier":
                return self.model_manager.incident_classifier.model
            elif model_name == "false_positive_filter":
                return self.model_manager.false_positive_filter.model
            elif model_name == "pattern_recognizer":
                return self.model_manager.pattern_recognizer.vectorizer
            else:
                logger.warning(f"Unknown model name: {model_name}")
                return None
        except Exception as e:
            logger.error(f"Error getting retrained model {model_name}: {e}")
            return None

    async def _deploy_models(self, registration_results: Dict[str, Any]) -> Dict[str, Any]:
        """Deploys successfully registered models."""
        deployment_results = {}
        
        for model_name, registration_result in registration_results.items():
            if not registration_result["success"]:
                deployment_results[model_name] = {
                    "success": False,
                    "error": "Model registration failed"
                }
                continue
            
            try:
                version = registration_result["version"]
                
                # Deploy model
                success = await self.model_registry.deploy_model(
                    model_name=model_name,
                    version=version,
                    environment="production"
                )
                
                if success:
                    deployment_results[model_name] = {
                        "success": True,
                        "version": version,
                        "environment": "production",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    logger.info(f"Successfully deployed {model_name} version {version}")
                else:
                    deployment_results[model_name] = {
                        "success": False,
                        "error": "Deployment failed"
                    }
                
            except Exception as e:
                logger.error(f"Failed to deploy {model_name}: {e}")
                deployment_results[model_name] = {
                    "success": False,
                    "error": str(e)
                }
        
        return deployment_results

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Gets the current status of the retraining pipeline."""
        return {
            **self.pipeline_stats,
            "pipeline_enabled": SETTINGS.auto_retrain_enabled,
            "retraining_interval_hours": SETTINGS.retrain_interval_hours,
            "performance_based_retraining": SETTINGS.performance_based_retraining,
            "drift_based_retraining": SETTINGS.drift_based_retraining,
            "feedback_based_retraining": SETTINGS.feedback_based_retraining
        }

    async def get_pipeline_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Gets the pipeline execution history."""
        # This would typically be stored in a database
        # For now, return the last run info
        if self.pipeline_stats["last_run"]:
            return [self.pipeline_stats["last_run"]]
        return []

    async def force_pipeline_run(self, reason: str = "Manual trigger") -> Dict[str, Any]:
        """Forces a pipeline run."""
        return await self.run_full_pipeline(trigger_reason=reason)
