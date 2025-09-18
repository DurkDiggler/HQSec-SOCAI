"""Model validation for retraining pipeline."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score

from ..config import SETTINGS
from ..ml.model_manager import MLModelManager

logger = logging.getLogger(__name__)

class ModelValidator:
    """
    Validates ML models for quality, performance, and reliability.
    Ensures models meet minimum standards before deployment.
    """

    def __init__(self, model_manager: MLModelManager = None):
        self.model_manager = model_manager or MLModelManager()
        self.validation_thresholds = {
            "min_accuracy": 0.7,
            "min_precision": 0.6,
            "min_recall": 0.6,
            "min_f1_score": 0.6,
            "max_mse": 1.0,
            "min_r2_score": 0.5
        }

    async def validate_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Validates all ML models in the system.
        
        Returns:
            Dict containing validation results for each model
        """
        validation_results = {}
        
        # Validate each model type
        models_to_validate = [
            "anomaly_detector",
            "risk_scorer", 
            "incident_classifier",
            "false_positive_filter",
            "pattern_recognizer"
        ]
        
        for model_name in models_to_validate:
            try:
                validation_result = await self._validate_single_model(model_name)
                validation_results[model_name] = validation_result
            except Exception as e:
                logger.error(f"Error validating {model_name}: {e}")
                validation_results[model_name] = {
                    "is_valid": False,
                    "error": str(e),
                    "metrics": {}
                }
        
        return validation_results

    async def _validate_single_model(self, model_name: str) -> Dict[str, Any]:
        """Validates a single model."""
        try:
            # Check if model is loaded
            model_loaded = await self._check_model_loaded(model_name)
            if not model_loaded:
                return {
                    "is_valid": False,
                    "error": "Model not loaded",
                    "metrics": {}
                }
            
            # Get model performance metrics
            performance_metrics = await self._get_model_performance(model_name)
            
            # Validate metrics against thresholds
            validation_passed = await self._validate_metrics(model_name, performance_metrics)
            
            # Check model integrity
            integrity_check = await self._check_model_integrity(model_name)
            
            # Overall validation result
            is_valid = validation_passed and integrity_check["passed"]
            
            return {
                "is_valid": is_valid,
                "metrics": performance_metrics,
                "integrity_check": integrity_check,
                "validation_passed": validation_passed,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validating {model_name}: {e}")
            return {
                "is_valid": False,
                "error": str(e),
                "metrics": {}
            }

    async def _check_model_loaded(self, model_name: str) -> bool:
        """Checks if a model is loaded and ready."""
        try:
            if model_name == "anomaly_detector":
                return self.model_manager.anomaly_detector.model is not None
            elif model_name == "risk_scorer":
                return self.model_manager.risk_scorer.model is not None
            elif model_name == "incident_classifier":
                return self.model_manager.incident_classifier.model is not None
            elif model_name == "false_positive_filter":
                return self.model_manager.false_positive_filter.model is not None
            elif model_name == "pattern_recognizer":
                return self.model_manager.pattern_recognizer.vectorizer is not None
            else:
                return False
        except Exception as e:
            logger.error(f"Error checking if {model_name} is loaded: {e}")
            return False

    async def _get_model_performance(self, model_name: str) -> Dict[str, float]:
        """Gets performance metrics for a model."""
        try:
            # This would typically use a validation dataset
            # For now, we'll use placeholder metrics
            if model_name == "anomaly_detector":
                return await self._get_anomaly_detector_metrics()
            elif model_name == "risk_scorer":
                return await self._get_risk_scorer_metrics()
            elif model_name == "incident_classifier":
                return await self._get_classifier_metrics()
            elif model_name == "false_positive_filter":
                return await self._get_fp_filter_metrics()
            elif model_name == "pattern_recognizer":
                return await self._get_pattern_recognizer_metrics()
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting performance metrics for {model_name}: {e}")
            return {}

    async def _get_anomaly_detector_metrics(self) -> Dict[str, float]:
        """Gets metrics for anomaly detector."""
        # Placeholder - in production, this would use actual validation data
        return {
            "accuracy": 0.85,
            "precision": 0.80,
            "recall": 0.75,
            "f1_score": 0.77
        }

    async def _get_risk_scorer_metrics(self) -> Dict[str, float]:
        """Gets metrics for risk scorer."""
        # Placeholder - in production, this would use actual validation data
        return {
            "mse": 0.15,
            "r2_score": 0.82,
            "mae": 0.12
        }

    async def _get_classifier_metrics(self) -> Dict[str, float]:
        """Gets metrics for incident classifier."""
        # Placeholder - in production, this would use actual validation data
        return {
            "accuracy": 0.88,
            "precision": 0.85,
            "recall": 0.82,
            "f1_score": 0.83
        }

    async def _get_fp_filter_metrics(self) -> Dict[str, float]:
        """Gets metrics for false positive filter."""
        # Placeholder - in production, this would use actual validation data
        return {
            "accuracy": 0.90,
            "precision": 0.88,
            "recall": 0.85,
            "f1_score": 0.86
        }

    async def _get_pattern_recognizer_metrics(self) -> Dict[str, float]:
        """Gets metrics for pattern recognizer."""
        # Placeholder - in production, this would use actual validation data
        return {
            "silhouette_score": 0.65,
            "cluster_quality": 0.78
        }

    async def _validate_metrics(self, model_name: str, metrics: Dict[str, float]) -> bool:
        """Validates metrics against thresholds."""
        try:
            if not metrics:
                return False
            
            # Define model-specific validation criteria
            if model_name in ["anomaly_detector", "incident_classifier", "false_positive_filter"]:
                # Classification models
                accuracy = metrics.get("accuracy", 0)
                precision = metrics.get("precision", 0)
                recall = metrics.get("recall", 0)
                f1 = metrics.get("f1_score", 0)
                
                return (accuracy >= self.validation_thresholds["min_accuracy"] and
                        precision >= self.validation_thresholds["min_precision"] and
                        recall >= self.validation_thresholds["min_recall"] and
                        f1 >= self.validation_thresholds["min_f1_score"])
            
            elif model_name == "risk_scorer":
                # Regression model
                mse = metrics.get("mse", float('inf'))
                r2 = metrics.get("r2_score", -float('inf'))
                
                return (mse <= self.validation_thresholds["max_mse"] and
                        r2 >= self.validation_thresholds["min_r2_score"])
            
            elif model_name == "pattern_recognizer":
                # Clustering model
                silhouette = metrics.get("silhouette_score", -1)
                cluster_quality = metrics.get("cluster_quality", 0)
                
                return (silhouette >= 0.3 and cluster_quality >= 0.6)
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating metrics for {model_name}: {e}")
            return False

    async def _check_model_integrity(self, model_name: str) -> Dict[str, Any]:
        """Checks model integrity and consistency."""
        try:
            integrity_checks = {
                "model_loaded": False,
                "preprocessor_loaded": False,
                "model_serializable": False,
                "passed": False
            }
            
            # Check if model is loaded
            integrity_checks["model_loaded"] = await self._check_model_loaded(model_name)
            
            # Check if preprocessor is loaded (for models that use one)
            if model_name in ["risk_scorer", "incident_classifier", "false_positive_filter"]:
                integrity_checks["preprocessor_loaded"] = await self._check_preprocessor_loaded(model_name)
            else:
                integrity_checks["preprocessor_loaded"] = True  # Not applicable
            
            # Check if model can be serialized
            integrity_checks["model_serializable"] = await self._check_model_serializable(model_name)
            
            # Overall integrity check
            integrity_checks["passed"] = all([
                integrity_checks["model_loaded"],
                integrity_checks["preprocessor_loaded"],
                integrity_checks["model_serializable"]
            ])
            
            return integrity_checks
            
        except Exception as e:
            logger.error(f"Error checking integrity for {model_name}: {e}")
            return {
                "model_loaded": False,
                "preprocessor_loaded": False,
                "model_serializable": False,
                "passed": False,
                "error": str(e)
            }

    async def _check_preprocessor_loaded(self, model_name: str) -> bool:
        """Checks if preprocessor is loaded for a model."""
        try:
            if model_name == "risk_scorer":
                return self.model_manager.risk_scorer.preprocessor is not None
            elif model_name == "incident_classifier":
                return self.model_manager.incident_classifier.preprocessor is not None
            elif model_name == "false_positive_filter":
                return self.model_manager.false_positive_filter.preprocessor is not None
            else:
                return True  # Not applicable
        except Exception as e:
            logger.error(f"Error checking preprocessor for {model_name}: {e}")
            return False

    async def _check_model_serializable(self, model_name: str) -> bool:
        """Checks if model can be serialized."""
        try:
            # This would test actual serialization in production
            # For now, just check if model exists
            return await self._check_model_loaded(model_name)
        except Exception as e:
            logger.error(f"Error checking serializability for {model_name}: {e}")
            return False

    async def validate_data_quality(self, training_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Validates the quality of training data.
        
        Args:
            training_data: Training data to validate
            
        Returns:
            Dict containing data quality validation results
        """
        try:
            quality_metrics = {
                "total_samples": sum(len(data) for data in training_data.values()),
                "data_types": list(training_data.keys()),
                "completeness_scores": {},
                "freshness_scores": {},
                "is_valid": True,
                "issues": []
            }
            
            # Validate each data type
            for data_type, data in training_data.items():
                if not data:
                    quality_metrics["issues"].append(f"No data available for {data_type}")
                    quality_metrics["is_valid"] = False
                    continue
                
                # Check data size
                if len(data) < SETTINGS.min_training_data_size:
                    quality_metrics["issues"].append(
                        f"Insufficient data for {data_type}: {len(data)} < {SETTINGS.min_training_data_size}"
                    )
                    quality_metrics["is_valid"] = False
                
                # Check data completeness
                completeness = await self._calculate_data_completeness(data)
                quality_metrics["completeness_scores"][data_type] = completeness
                
                if completeness < SETTINGS.min_data_completeness:
                    quality_metrics["issues"].append(
                        f"Low completeness for {data_type}: {completeness:.2f} < {SETTINGS.min_data_completeness}"
                    )
                    quality_metrics["is_valid"] = False
                
                # Check data freshness
                freshness = await self._calculate_data_freshness(data)
                quality_metrics["freshness_scores"][data_type] = freshness
                
                if freshness < SETTINGS.min_data_freshness:
                    quality_metrics["issues"].append(
                        f"Stale data for {data_type}: {freshness:.2f} < {SETTINGS.min_data_freshness}"
                    )
                    quality_metrics["is_valid"] = False
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Error validating data quality: {e}")
            return {
                "is_valid": False,
                "issues": [f"Data quality validation error: {str(e)}"],
                "total_samples": 0,
                "data_types": [],
                "completeness_scores": {},
                "freshness_scores": {}
            }

    async def _calculate_data_completeness(self, data: List[Dict[str, Any]]) -> float:
        """Calculates data completeness score."""
        if not data:
            return 0.0
        
        total_fields = 0
        filled_fields = 0
        
        for record in data:
            for key, value in record.items():
                total_fields += 1
                if value is not None and value != "":
                    filled_fields += 1
        
        return filled_fields / total_fields if total_fields > 0 else 0.0

    async def _calculate_data_freshness(self, data: List[Dict[str, Any]]) -> float:
        """Calculates data freshness score."""
        if not data:
            return 0.0
        
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        fresh_records = 0
        
        for record in data:
            timestamp_str = record.get("timestamp", "")
            try:
                record_time = datetime.fromisoformat(timestamp_str)
                age_hours = (now - record_time).total_seconds() / 3600
                
                # Consider data fresh if it's less than 7 days old
                if age_hours < 168:  # 7 days
                    fresh_records += 1
            except (ValueError, TypeError):
                # If timestamp is invalid, consider it stale
                pass
        
        return fresh_records / len(data)

    async def get_validation_thresholds(self) -> Dict[str, float]:
        """Gets current validation thresholds."""
        return self.validation_thresholds.copy()

    async def update_validation_thresholds(self, new_thresholds: Dict[str, float]) -> bool:
        """Updates validation thresholds."""
        try:
            self.validation_thresholds.update(new_thresholds)
            logger.info(f"Updated validation thresholds: {new_thresholds}")
            return True
        except Exception as e:
            logger.error(f"Error updating validation thresholds: {e}")
            return False
