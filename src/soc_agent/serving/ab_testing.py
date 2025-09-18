"""A/B Testing framework for ML model performance comparison."""

from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from ..config import SETTINGS
from ..database import get_db, save_ab_test_result, get_ab_test_results

logger = logging.getLogger(__name__)

class ABTestingFramework:
    """
    A/B Testing framework for comparing ML model performance.
    Supports statistical significance testing and performance metrics.
    """

    def __init__(self):
        self.active_tests: Dict[str, Dict[str, Any]] = {}
        self.test_results: Dict[str, List[Dict[str, Any]]] = {}

    async def create_ab_test(self, 
                            test_name: str,
                            model_a: str,
                            model_b: str,
                            traffic_split: float = 0.5,
                            success_metric: str = "accuracy",
                            minimum_sample_size: int = 1000,
                            significance_level: float = 0.05) -> str:
        """
        Creates a new A/B test for comparing two models.
        
        Args:
            test_name: Unique name for the test
            model_a: Name of model A (control)
            model_b: Name of model B (treatment)
            traffic_split: Fraction of traffic for model B (0.0-1.0)
            success_metric: Metric to optimize (accuracy, precision, recall, f1, etc.)
            minimum_sample_size: Minimum samples needed for statistical significance
            significance_level: Statistical significance level (alpha)
            
        Returns:
            str: Test ID
        """
        test_id = f"ab_test_{test_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        test_config = {
            "test_id": test_id,
            "test_name": test_name,
            "model_a": model_a,
            "model_b": model_b,
            "traffic_split": traffic_split,
            "success_metric": success_metric,
            "minimum_sample_size": minimum_sample_size,
            "significance_level": significance_level,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "results_a": [],
            "results_b": [],
            "total_samples": 0
        }
        
        self.active_tests[test_id] = test_config
        logger.info(f"Created A/B test {test_id}: {model_a} vs {model_b}")
        
        return test_id

    async def assign_model(self, test_id: str, user_id: str = None) -> str:
        """
        Assigns a model variant for a given user/request.
        
        Args:
            test_id: A/B test ID
            user_id: User ID for consistent assignment (optional)
            
        Returns:
            str: Assigned model name
        """
        if test_id not in self.active_tests:
            raise ValueError(f"A/B test {test_id} not found")
        
        test = self.active_tests[test_id]
        
        # Use user_id for consistent assignment if provided
        if user_id:
            # Use hash of user_id for consistent assignment
            hash_value = hash(user_id) % 1000
            threshold = test["traffic_split"] * 1000
            model = test["model_b"] if hash_value < threshold else test["model_a"]
        else:
            # Random assignment
            model = test["model_b"] if random.random() < test["traffic_split"] else test["model_a"]
        
        return model

    async def record_result(self, 
                           test_id: str, 
                           model_name: str,
                           prediction: Any,
                           ground_truth: Any,
                           metadata: Dict[str, Any] = None) -> bool:
        """
        Records a prediction result for A/B test analysis.
        
        Args:
            test_id: A/B test ID
            model_name: Name of the model that made the prediction
            prediction: Model prediction
            ground_truth: True label/outcome
            metadata: Additional metadata
            
        Returns:
            bool: True if recorded successfully
        """
        if test_id not in self.active_tests:
            logger.error(f"A/B test {test_id} not found")
            return False
        
        test = self.active_tests[test_id]
        
        # Calculate metrics
        metrics = await self._calculate_metrics(prediction, ground_truth, test["success_metric"])
        
        result = {
            "test_id": test_id,
            "model_name": model_name,
            "prediction": prediction,
            "ground_truth": ground_truth,
            "metrics": metrics,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store result
        if model_name == test["model_a"]:
            test["results_a"].append(result)
        elif model_name == test["model_b"]:
            test["results_b"].append(result)
        else:
            logger.warning(f"Unknown model {model_name} for test {test_id}")
            return False
        
        test["total_samples"] += 1
        
        # Save to database
        with get_db() as db:
            save_ab_test_result(db, result)
        
        logger.debug(f"Recorded result for test {test_id}, model {model_name}")
        return True

    async def _calculate_metrics(self, prediction: Any, ground_truth: Any, metric: str) -> float:
        """
        Calculates the specified metric for a prediction.
        
        Args:
            prediction: Model prediction
            ground_truth: True label
            metric: Metric name
            
        Returns:
            float: Calculated metric value
        """
        try:
            if metric == "accuracy":
                return float(prediction == ground_truth)
            elif metric == "precision":
                # For binary classification
                if prediction == 1 and ground_truth == 1:
                    return 1.0
                elif prediction == 1 and ground_truth == 0:
                    return 0.0
                else:
                    return None  # Not applicable
            elif metric == "recall":
                # For binary classification
                if ground_truth == 1 and prediction == 1:
                    return 1.0
                elif ground_truth == 1 and prediction == 0:
                    return 0.0
                else:
                    return None  # Not applicable
            elif metric == "f1":
                precision = await self._calculate_metrics(prediction, ground_truth, "precision")
                recall = await self._calculate_metrics(prediction, ground_truth, "recall")
                if precision is not None and recall is not None and (precision + recall) > 0:
                    return 2 * (precision * recall) / (precision + recall)
                return None
            elif metric == "mse":
                # For regression
                return float((prediction - ground_truth) ** 2)
            elif metric == "mae":
                # For regression
                return float(abs(prediction - ground_truth))
            else:
                logger.warning(f"Unknown metric: {metric}")
                return 0.0
        except Exception as e:
            logger.error(f"Error calculating metric {metric}: {e}")
            return 0.0

    async def analyze_test(self, test_id: str) -> Dict[str, Any]:
        """
        Analyzes A/B test results and determines statistical significance.
        
        Args:
            test_id: A/B test ID
            
        Returns:
            Dict containing analysis results
        """
        if test_id not in self.active_tests:
            raise ValueError(f"A/B test {test_id} not found")
        
        test = self.active_tests[test_id]
        
        # Check if we have enough samples
        if test["total_samples"] < test["minimum_sample_size"]:
            return {
                "test_id": test_id,
                "status": "insufficient_data",
                "message": f"Need {test['minimum_sample_size']} samples, have {test['total_samples']}",
                "total_samples": test["total_samples"],
                "minimum_required": test["minimum_sample_size"]
            }
        
        # Extract metrics for each model
        metrics_a = [r["metrics"] for r in test["results_a"] if r["metrics"] is not None]
        metrics_b = [r["metrics"] for r in test["results_b"] if r["metrics"] is not None]
        
        if not metrics_a or not metrics_b:
            return {
                "test_id": test_id,
                "status": "no_valid_metrics",
                "message": "No valid metrics found for analysis"
            }
        
        # Calculate summary statistics
        mean_a = np.mean(metrics_a)
        mean_b = np.mean(metrics_b)
        std_a = np.std(metrics_a)
        std_b = np.std(metrics_b)
        
        # Perform statistical test
        try:
            # Use appropriate test based on data distribution
            if len(metrics_a) > 30 and len(metrics_b) > 30:
                # Use t-test for large samples
                t_stat, p_value = stats.ttest_ind(metrics_a, metrics_b)
                test_type = "t-test"
            else:
                # Use Mann-Whitney U test for small samples or non-normal data
                u_stat, p_value = stats.mannwhitneyu(metrics_a, metrics_b, alternative='two-sided')
                test_type = "mann-whitney-u"
            
            # Determine significance
            is_significant = p_value < test["significance_level"]
            
            # Calculate effect size (Cohen's d)
            pooled_std = np.sqrt(((len(metrics_a) - 1) * std_a**2 + (len(metrics_b) - 1) * std_b**2) / 
                                (len(metrics_a) + len(metrics_b) - 2))
            cohens_d = (mean_b - mean_a) / pooled_std if pooled_std > 0 else 0
            
            # Determine winner
            winner = "model_b" if mean_b > mean_a else "model_a"
            improvement = abs(mean_b - mean_a) / mean_a * 100 if mean_a != 0 else 0
            
            analysis_result = {
                "test_id": test_id,
                "status": "completed",
                "test_type": test_type,
                "model_a": {
                    "name": test["model_a"],
                    "mean": round(mean_a, 4),
                    "std": round(std_a, 4),
                    "sample_size": len(metrics_a)
                },
                "model_b": {
                    "name": test["model_b"],
                    "mean": round(mean_b, 4),
                    "std": round(std_b, 4),
                    "sample_size": len(metrics_b)
                },
                "statistical_test": {
                    "p_value": round(p_value, 6),
                    "is_significant": is_significant,
                    "significance_level": test["significance_level"]
                },
                "effect_size": {
                    "cohens_d": round(cohens_d, 4),
                    "interpretation": self._interpret_effect_size(cohens_d)
                },
                "winner": winner,
                "improvement_percent": round(improvement, 2),
                "total_samples": test["total_samples"],
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            # Store analysis result
            self.test_results[test_id] = analysis_result
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing A/B test {test_id}: {e}")
            return {
                "test_id": test_id,
                "status": "analysis_error",
                "message": str(e)
            }

    def _interpret_effect_size(self, cohens_d: float) -> str:
        """Interprets Cohen's d effect size."""
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"

    async def get_test_status(self, test_id: str) -> Dict[str, Any]:
        """Gets the current status of an A/B test."""
        if test_id not in self.active_tests:
            return {"error": f"A/B test {test_id} not found"}
        
        test = self.active_tests[test_id]
        return {
            "test_id": test_id,
            "status": test["status"],
            "total_samples": test["total_samples"],
            "minimum_required": test["minimum_sample_size"],
            "progress_percent": min(100, (test["total_samples"] / test["minimum_sample_size"]) * 100),
            "model_a_samples": len(test["results_a"]),
            "model_b_samples": len(test["results_b"])
        }

    async def stop_test(self, test_id: str) -> bool:
        """Stops an active A/B test."""
        if test_id not in self.active_tests:
            return False
        
        self.active_tests[test_id]["status"] = "stopped"
        logger.info(f"A/B test {test_id} stopped")
        return True

    async def get_all_tests(self) -> List[Dict[str, Any]]:
        """Gets information about all A/B tests."""
        return [
            {
                "test_id": test_id,
                "test_name": test["test_name"],
                "model_a": test["model_a"],
                "model_b": test["model_b"],
                "status": test["status"],
                "total_samples": test["total_samples"],
                "created_at": test["created_at"]
            }
            for test_id, test in self.active_tests.items()
        ]

    async def get_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Gets the analysis results for a completed A/B test."""
        return self.test_results.get(test_id)
