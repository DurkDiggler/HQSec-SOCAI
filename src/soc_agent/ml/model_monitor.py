"""ML model performance monitoring and drift detection."""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
from collections import deque

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy import stats
from scipy.stats import ks_2samp

from ..config import SETTINGS

logger = logging.getLogger(__name__)


class ModelMonitor:
    """ML model performance monitoring and drift detection."""
    
    def __init__(self):
        self.performance_history = {}
        self.drift_detection_history = {}
        self.alert_thresholds = {
            'accuracy': 0.8,
            'precision': 0.8,
            'recall': 0.8,
            'f1_score': 0.8,
            'mse': 0.1,
            'mae': 0.1,
            'r2_score': 0.8
        }
        self.drift_threshold = SETTINGS.model_drift_threshold
        self.performance_threshold = SETTINGS.model_performance_threshold
        
        # Initialize monitoring data structures
        self._initialize_monitoring()
    
    def _initialize_monitoring(self):
        """Initialize monitoring data structures."""
        self.performance_history = {
            'anomaly_detector': deque(maxlen=1000),
            'risk_scorer': deque(maxlen=1000),
            'incident_classifier': deque(maxlen=1000),
            'false_positive_filter': deque(maxlen=1000),
            'pattern_recognizer': deque(maxlen=1000)
        }
        
        self.drift_detection_history = {
            'anomaly_detector': deque(maxlen=100),
            'risk_scorer': deque(maxlen=100),
            'incident_classifier': deque(maxlen=100),
            'false_positive_filter': deque(maxlen=100),
            'pattern_recognizer': deque(maxlen=100)
        }
    
    async def monitor_model_performance(
        self, 
        model_name: str, 
        predictions: List[Any], 
        actual_values: List[Any],
        model_type: str = 'classification'
    ) -> Dict[str, Any]:
        """Monitor model performance and detect degradation."""
        try:
            if not predictions or not actual_values:
                return {'status': 'skipped', 'reason': 'No data provided'}
            
            # Calculate performance metrics
            metrics = self._calculate_performance_metrics(
                predictions, actual_values, model_type
            )
            
            # Store performance history
            performance_entry = {
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics,
                'sample_count': len(predictions)
            }
            self.performance_history[model_name].append(performance_entry)
            
            # Check for performance degradation
            degradation_alerts = self._check_performance_degradation(
                model_name, metrics
            )
            
            # Calculate performance trend
            trend = self._calculate_performance_trend(model_name)
            
            return {
                'status': 'success',
                'model_name': model_name,
                'metrics': metrics,
                'degradation_alerts': degradation_alerts,
                'trend': trend,
                'monitoring_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance monitoring failed for {model_name}: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def detect_data_drift(
        self, 
        model_name: str, 
        current_data: np.ndarray, 
        reference_data: np.ndarray
    ) -> Dict[str, Any]:
        """Detect data drift between current and reference data."""
        try:
            if current_data.shape[1] != reference_data.shape[1]:
                return {
                    'status': 'error',
                    'message': 'Feature dimensions do not match'
                }
            
            # Calculate drift metrics
            drift_metrics = self._calculate_drift_metrics(
                current_data, reference_data
            )
            
            # Store drift detection history
            drift_entry = {
                'timestamp': datetime.now().isoformat(),
                'drift_metrics': drift_metrics,
                'sample_count': len(current_data)
            }
            self.drift_detection_history[model_name].append(drift_entry)
            
            # Check for significant drift
            drift_alerts = self._check_drift_alerts(drift_metrics)
            
            # Calculate drift trend
            trend = self._calculate_drift_trend(model_name)
            
            return {
                'status': 'success',
                'model_name': model_name,
                'drift_metrics': drift_metrics,
                'drift_alerts': drift_alerts,
                'trend': trend,
                'detection_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Drift detection failed for {model_name}: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def monitor_prediction_confidence(
        self, 
        model_name: str, 
        predictions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Monitor prediction confidence levels."""
        try:
            if not predictions:
                return {'status': 'skipped', 'reason': 'No predictions provided'}
            
            # Extract confidence scores
            confidence_scores = []
            for pred in predictions:
                if 'confidence' in pred:
                    confidence_scores.append(pred['confidence'])
                elif 'anomaly_score' in pred:
                    confidence_scores.append(pred['anomaly_score'])
                elif 'risk_score' in pred:
                    confidence_scores.append(pred['risk_score'] / 100.0)
            
            if not confidence_scores:
                return {'status': 'skipped', 'reason': 'No confidence scores found'}
            
            # Calculate confidence metrics
            confidence_metrics = {
                'mean_confidence': float(np.mean(confidence_scores)),
                'std_confidence': float(np.std(confidence_scores)),
                'min_confidence': float(np.min(confidence_scores)),
                'max_confidence': float(np.max(confidence_scores)),
                'low_confidence_count': len([c for c in confidence_scores if c < 0.5]),
                'high_confidence_count': len([c for c in confidence_scores if c > 0.8])
            }
            
            # Check for confidence issues
            confidence_alerts = self._check_confidence_alerts(confidence_metrics)
            
            return {
                'status': 'success',
                'model_name': model_name,
                'confidence_metrics': confidence_metrics,
                'confidence_alerts': confidence_alerts,
                'monitoring_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Confidence monitoring failed for {model_name}: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _calculate_performance_metrics(
        self, 
        predictions: List[Any], 
        actual_values: List[Any], 
        model_type: str
    ) -> Dict[str, float]:
        """Calculate performance metrics based on model type."""
        try:
            metrics = {}
            
            if model_type == 'classification':
                # Classification metrics
                metrics['accuracy'] = float(accuracy_score(actual_values, predictions))
                metrics['precision'] = float(precision_score(actual_values, predictions, average='weighted', zero_division=0))
                metrics['recall'] = float(recall_score(actual_values, predictions, average='weighted', zero_division=0))
                metrics['f1_score'] = float(f1_score(actual_values, predictions, average='weighted', zero_division=0))
                
            elif model_type == 'regression':
                # Regression metrics
                metrics['mse'] = float(mean_squared_error(actual_values, predictions))
                metrics['mae'] = float(mean_absolute_error(actual_values, predictions))
                metrics['r2_score'] = float(r2_score(actual_values, predictions))
                
            else:
                # Generic metrics
                metrics['mse'] = float(mean_squared_error(actual_values, predictions))
                metrics['mae'] = float(mean_absolute_error(actual_values, predictions))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Performance metrics calculation failed: {e}")
            return {}
    
    def _calculate_drift_metrics(
        self, 
        current_data: np.ndarray, 
        reference_data: np.ndarray
    ) -> Dict[str, float]:
        """Calculate drift metrics between current and reference data."""
        try:
            metrics = {}
            
            # Statistical tests for each feature
            feature_drifts = []
            for i in range(current_data.shape[1]):
                try:
                    # Kolmogorov-Smirnov test
                    ks_stat, ks_pvalue = ks_2samp(
                        reference_data[:, i], current_data[:, i]
                    )
                    feature_drifts.append(ks_stat)
                except:
                    feature_drifts.append(0.0)
            
            # Overall drift metrics
            metrics['mean_feature_drift'] = float(np.mean(feature_drifts))
            metrics['max_feature_drift'] = float(np.max(feature_drifts))
            metrics['drift_features_count'] = int(np.sum(np.array(feature_drifts) > 0.1))
            metrics['total_features'] = current_data.shape[1]
            
            # Distribution statistics
            metrics['current_mean'] = float(np.mean(current_data))
            metrics['reference_mean'] = float(np.mean(reference_data))
            metrics['current_std'] = float(np.std(current_data))
            metrics['reference_std'] = float(np.std(reference_data))
            
            # Overall drift score
            metrics['overall_drift_score'] = float(np.mean(feature_drifts))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Drift metrics calculation failed: {e}")
            return {}
    
    def _check_performance_degradation(
        self, 
        model_name: str, 
        current_metrics: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Check for performance degradation."""
        alerts = []
        
        try:
            # Get historical performance
            history = list(self.performance_history[model_name])
            if len(history) < 2:
                return alerts
            
            # Calculate baseline performance
            baseline_metrics = {}
            for metric_name in current_metrics.keys():
                if metric_name in self.alert_thresholds:
                    baseline_metrics[metric_name] = np.mean([
                        entry['metrics'].get(metric_name, 0) 
                        for entry in history[-10:]  # Last 10 entries
                    ])
            
            # Check for degradation
            for metric_name, current_value in current_metrics.items():
                if metric_name in baseline_metrics:
                    baseline_value = baseline_metrics[metric_name]
                    threshold = self.alert_thresholds.get(metric_name, 0.8)
                    
                    # Check if current performance is below threshold
                    if current_value < threshold:
                        alerts.append({
                            'type': 'performance_degradation',
                            'metric': metric_name,
                            'current_value': current_value,
                            'threshold': threshold,
                            'severity': 'HIGH' if current_value < threshold * 0.8 else 'MEDIUM'
                        })
                    
                    # Check if performance has significantly degraded
                    degradation = (baseline_value - current_value) / baseline_value
                    if degradation > 0.2:  # 20% degradation
                        alerts.append({
                            'type': 'performance_degradation',
                            'metric': metric_name,
                            'current_value': current_value,
                            'baseline_value': baseline_value,
                            'degradation_percent': degradation * 100,
                            'severity': 'HIGH' if degradation > 0.4 else 'MEDIUM'
                        })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Performance degradation check failed: {e}")
            return []
    
    def _check_drift_alerts(self, drift_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check for data drift alerts."""
        alerts = []
        
        try:
            # Check overall drift score
            overall_drift = drift_metrics.get('overall_drift_score', 0)
            if overall_drift > self.drift_threshold:
                alerts.append({
                    'type': 'data_drift',
                    'metric': 'overall_drift_score',
                    'value': overall_drift,
                    'threshold': self.drift_threshold,
                    'severity': 'HIGH' if overall_drift > self.drift_threshold * 1.5 else 'MEDIUM'
                })
            
            # Check feature drift
            drift_features = drift_metrics.get('drift_features_count', 0)
            total_features = drift_metrics.get('total_features', 1)
            drift_ratio = drift_features / total_features
            
            if drift_ratio > 0.3:  # 30% of features showing drift
                alerts.append({
                    'type': 'feature_drift',
                    'metric': 'drift_features_ratio',
                    'value': drift_ratio,
                    'drift_features_count': drift_features,
                    'total_features': total_features,
                    'severity': 'HIGH' if drift_ratio > 0.5 else 'MEDIUM'
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Drift alert check failed: {e}")
            return []
    
    def _check_confidence_alerts(self, confidence_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check for confidence-related alerts."""
        alerts = []
        
        try:
            mean_confidence = confidence_metrics.get('mean_confidence', 0)
            low_confidence_count = confidence_metrics.get('low_confidence_count', 0)
            
            # Check for low overall confidence
            if mean_confidence < 0.5:
                alerts.append({
                    'type': 'low_confidence',
                    'metric': 'mean_confidence',
                    'value': mean_confidence,
                    'threshold': 0.5,
                    'severity': 'HIGH' if mean_confidence < 0.3 else 'MEDIUM'
                })
            
            # Check for high number of low-confidence predictions
            if low_confidence_count > 10:  # More than 10 low-confidence predictions
                alerts.append({
                    'type': 'high_low_confidence_count',
                    'metric': 'low_confidence_count',
                    'value': low_confidence_count,
                    'threshold': 10,
                    'severity': 'MEDIUM'
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Confidence alert check failed: {e}")
            return []
    
    def _calculate_performance_trend(self, model_name: str) -> Dict[str, Any]:
        """Calculate performance trend over time."""
        try:
            history = list(self.performance_history[model_name])
            if len(history) < 3:
                return {'trend': 'insufficient_data'}
            
            # Extract metrics over time
            timestamps = [entry['timestamp'] for entry in history]
            metrics_over_time = {}
            
            for entry in history:
                for metric_name, value in entry['metrics'].items():
                    if metric_name not in metrics_over_time:
                        metrics_over_time[metric_name] = []
                    metrics_over_time[metric_name].append(value)
            
            # Calculate trends
            trends = {}
            for metric_name, values in metrics_over_time.items():
                if len(values) >= 3:
                    # Simple linear trend calculation
                    x = np.arange(len(values))
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
                    trends[metric_name] = {
                        'slope': float(slope),
                        'r_squared': float(r_value ** 2),
                        'trend': 'improving' if slope > 0.01 else 'degrading' if slope < -0.01 else 'stable'
                    }
            
            return {
                'trend': 'mixed' if len(set(t['trend'] for t in trends.values())) > 1 else list(trends.values())[0]['trend'] if trends else 'unknown',
                'metric_trends': trends
            }
            
        except Exception as e:
            logger.error(f"Performance trend calculation failed: {e}")
            return {'trend': 'error'}
    
    def _calculate_drift_trend(self, model_name: str) -> Dict[str, Any]:
        """Calculate drift trend over time."""
        try:
            history = list(self.drift_detection_history[model_name])
            if len(history) < 3:
                return {'trend': 'insufficient_data'}
            
            # Extract drift scores over time
            drift_scores = [entry['drift_metrics'].get('overall_drift_score', 0) for entry in history]
            
            if len(drift_scores) >= 3:
                x = np.arange(len(drift_scores))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, drift_scores)
                
                return {
                    'trend': 'increasing' if slope > 0.01 else 'decreasing' if slope < -0.01 else 'stable',
                    'slope': float(slope),
                    'r_squared': float(r_value ** 2)
                }
            else:
                return {'trend': 'insufficient_data'}
                
        except Exception as e:
            logger.error(f"Drift trend calculation failed: {e}")
            return {'trend': 'error'}
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary."""
        try:
            summary = {
                'monitoring_timestamp': datetime.now().isoformat(),
                'models': {}
            }
            
            for model_name in self.performance_history.keys():
                # Performance summary
                perf_history = list(self.performance_history[model_name])
                drift_history = list(self.drift_detection_history[model_name])
                
                model_summary = {
                    'performance_entries': len(perf_history),
                    'drift_entries': len(drift_history),
                    'last_performance_check': perf_history[-1]['timestamp'] if perf_history else None,
                    'last_drift_check': drift_history[-1]['timestamp'] if drift_history else None
                }
                
                # Recent performance
                if perf_history:
                    recent_metrics = perf_history[-1]['metrics']
                    model_summary['recent_performance'] = recent_metrics
                
                # Recent drift
                if drift_history:
                    recent_drift = drift_history[-1]['drift_metrics']
                    model_summary['recent_drift'] = recent_drift
                
                summary['models'][model_name] = model_summary
            
            return summary
            
        except Exception as e:
            logger.error(f"Monitoring summary generation failed: {e}")
            return {'error': str(e)}
    
    def save_monitoring_data(self, path: str = None) -> bool:
        """Save monitoring data to disk."""
        try:
            save_path = path or SETTINGS.ml_model_storage_path
            os.makedirs(save_path, exist_ok=True)
            
            # Save performance history
            perf_path = os.path.join(save_path, 'performance_history.json')
            with open(perf_path, 'w') as f:
                json.dump({
                    model_name: list(history) 
                    for model_name, history in self.performance_history.items()
                }, f, indent=2)
            
            # Save drift history
            drift_path = os.path.join(save_path, 'drift_history.json')
            with open(drift_path, 'w') as f:
                json.dump({
                    model_name: list(history) 
                    for model_name, history in self.drift_detection_history.items()
                }, f, indent=2)
            
            logger.info(f"Monitoring data saved to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save monitoring data: {e}")
            return False
    
    def load_monitoring_data(self, path: str = None) -> bool:
        """Load monitoring data from disk."""
        try:
            load_path = path or SETTINGS.ml_model_storage_path
            
            # Load performance history
            perf_path = os.path.join(load_path, 'performance_history.json')
            if os.path.exists(perf_path):
                with open(perf_path, 'r') as f:
                    perf_data = json.load(f)
                    for model_name, history in perf_data.items():
                        if model_name in self.performance_history:
                            self.performance_history[model_name] = deque(history, maxlen=1000)
            
            # Load drift history
            drift_path = os.path.join(load_path, 'drift_history.json')
            if os.path.exists(drift_path):
                with open(drift_path, 'r') as f:
                    drift_data = json.load(f)
                    for model_name, history in drift_data.items():
                        if model_name in self.drift_detection_history:
                            self.drift_detection_history[model_name] = deque(history, maxlen=100)
            
            logger.info(f"Monitoring data loaded from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load monitoring data: {e}")
            return False
