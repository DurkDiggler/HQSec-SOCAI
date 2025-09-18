"""ML model management and training pipeline."""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import joblib
import os
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .anomaly_detector import AnomalyDetector
from .risk_scorer import RiskScorer
from .incident_classifier import IncidentClassifier
from .false_positive_filter import FalsePositiveFilter
from .pattern_recognizer import PatternRecognizer

from ..config import SETTINGS

logger = logging.getLogger(__name__)


class ModelManager:
    """Centralized ML model management and training pipeline."""
    
    def __init__(self):
        self.models = {
            'anomaly_detector': AnomalyDetector(),
            'risk_scorer': RiskScorer(),
            'incident_classifier': IncidentClassifier(),
            'false_positive_filter': FalsePositiveFilter(),
            'pattern_recognizer': PatternRecognizer()
        }
        
        self.training_status = {}
        self.model_versions = {}
        self.performance_metrics = {}
        self.training_history = []
        
        # Initialize model storage
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize model storage directories."""
        try:
            os.makedirs(SETTINGS.ml_model_storage_path, exist_ok=True)
            os.makedirs(SETTINGS.ml_training_data_path, exist_ok=True)
            logger.info(f"Model storage initialized at {SETTINGS.ml_model_storage_path}")
        except Exception as e:
            logger.error(f"Failed to initialize model storage: {e}")
    
    async def train_all_models(self, training_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Train all ML models with provided training data."""
        try:
            logger.info("Starting training of all ML models...")
            
            training_results = {}
            training_tasks = []
            
            # Create training tasks for each model
            for model_name, model in self.models.items():
                if model_name in training_data:
                    task = self._train_model_async(model_name, model, training_data[model_name])
                    training_tasks.append(task)
            
            # Execute training tasks in parallel
            if training_tasks:
                results = await asyncio.gather(*training_tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    model_name = list(self.models.keys())[i]
                    if isinstance(result, Exception):
                        training_results[model_name] = {'status': 'failed', 'error': str(result)}
                    else:
                        training_results[model_name] = result
            else:
                logger.warning("No training data provided for any models")
                return {'status': 'failed', 'error': 'No training data provided'}
            
            # Update training status
            self.training_status = {
                model_name: result.get('status', 'unknown') 
                for model_name, result in training_results.items()
            }
            
            # Save training history
            self._save_training_history(training_results)
            
            logger.info("All ML model training completed")
            
            return {
                'status': 'success',
                'training_results': training_results,
                'training_status': self.training_status
            }
            
        except Exception as e:
            logger.error(f"Training all models failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _train_model_async(self, model_name: str, model: Any, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train a single model asynchronously."""
        try:
            logger.info(f"Training {model_name}...")
            
            # Train the model
            result = await model.train_models(training_data)
            
            # Save the model
            if result.get('status') == 'success':
                model.save_models()
                self.model_versions[model_name] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Training {model_name} failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def load_all_models(self) -> Dict[str, bool]:
        """Load all trained models from disk."""
        try:
            logger.info("Loading all ML models...")
            
            load_results = {}
            for model_name, model in self.models.items():
                try:
                    success = model.load_models()
                    load_results[model_name] = success
                    if success:
                        logger.info(f"Successfully loaded {model_name}")
                    else:
                        logger.warning(f"Failed to load {model_name}")
                except Exception as e:
                    logger.error(f"Error loading {model_name}: {e}")
                    load_results[model_name] = False
            
            return load_results
            
        except Exception as e:
            logger.error(f"Loading all models failed: {e}")
            return {}
    
    async def predict_anomaly(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict anomaly using the anomaly detector."""
        try:
            return await self.models['anomaly_detector'].detect_anomalies(event_data)
        except Exception as e:
            logger.error(f"Anomaly prediction failed: {e}")
            return {'error': str(e)}
    
    async def calculate_risk_score(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk score using the risk scorer."""
        try:
            return await self.models['risk_scorer'].calculate_risk_score(threat_data)
        except Exception as e:
            logger.error(f"Risk score calculation failed: {e}")
            return {'error': str(e)}
    
    async def classify_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify incident using the incident classifier."""
        try:
            return await self.models['incident_classifier'].classify_incident(incident_data)
        except Exception as e:
            logger.error(f"Incident classification failed: {e}")
            return {'error': str(e)}
    
    async def filter_false_positives(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter false positives using the false positive filter."""
        try:
            return await self.models['false_positive_filter'].filter_false_positives(alert_data)
        except Exception as e:
            logger.error(f"False positive filtering failed: {e}")
            return {'error': str(e)}
    
    async def detect_patterns(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect attack patterns using the pattern recognizer."""
        try:
            return await self.models['pattern_recognizer'].detect_attack_patterns(event_data)
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
            return {'error': str(e)}
    
    async def comprehensive_analysis(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive analysis using all models."""
        try:
            logger.info("Performing comprehensive analysis...")
            
            # Run all models in parallel
            tasks = [
                self.predict_anomaly(event_data),
                self.calculate_risk_score(event_data),
                self.classify_incident(event_data),
                self.filter_false_positives(event_data),
                self.detect_patterns(event_data)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Organize results
            analysis_results = {
                'anomaly_detection': results[0] if not isinstance(results[0], Exception) else {'error': str(results[0])},
                'risk_assessment': results[1] if not isinstance(results[1], Exception) else {'error': str(results[1])},
                'incident_classification': results[2] if not isinstance(results[2], Exception) else {'error': str(results[2])},
                'false_positive_filtering': results[3] if not isinstance(results[3], Exception) else {'error': str(results[3])},
                'pattern_recognition': results[4] if not isinstance(results[4], Exception) else {'error': str(results[4])}
            }
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(analysis_results)
            
            # Generate comprehensive recommendations
            recommendations = self._generate_comprehensive_recommendations(analysis_results)
            
            return {
                'analysis_results': analysis_results,
                'overall_confidence': overall_confidence,
                'recommendations': recommendations,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            return {'error': str(e)}
    
    def _calculate_overall_confidence(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate overall confidence from all analysis results."""
        try:
            confidences = []
            
            for model_name, result in analysis_results.items():
                if 'error' not in result:
                    if 'confidence' in result:
                        confidences.append(result['confidence'])
                    elif 'anomaly_score' in result:
                        confidences.append(result['anomaly_score'])
                    elif 'risk_score' in result:
                        confidences.append(result['risk_score'] / 100.0)
            
            if confidences:
                return float(np.mean(confidences))
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Overall confidence calculation failed: {e}")
            return 0.5
    
    def _generate_comprehensive_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive recommendations from all analysis results."""
        recommendations = []
        
        try:
            # Collect recommendations from all models
            for model_name, result in analysis_results.items():
                if 'error' not in result and 'recommendations' in result:
                    for rec in result['recommendations']:
                        rec['source_model'] = model_name
                        recommendations.append(rec)
            
            # Sort by priority
            priority_order = {'IMMEDIATE': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
            recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'LOW'), 3))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Comprehensive recommendation generation failed: {e}")
            return []
    
    def _save_training_history(self, training_results: Dict[str, Any]):
        """Save training history to disk."""
        try:
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'training_results': training_results,
                'model_versions': self.model_versions.copy()
            }
            
            self.training_history.append(history_entry)
            
            # Save to file
            history_path = os.path.join(SETTINGS.ml_model_storage_path, 'training_history.json')
            with open(history_path, 'w') as f:
                json.dump(self.training_history, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save training history: {e}")
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models."""
        try:
            status = {}
            
            for model_name, model in self.models.items():
                status[model_name] = {
                    'is_trained': getattr(model, 'is_trained', False),
                    'last_training': self.model_versions.get(model_name, 'Never'),
                    'training_status': self.training_status.get(model_name, 'Unknown')
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get model status: {e}")
            return {}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all models."""
        try:
            metrics = {}
            
            for model_name, model in self.models.items():
                if hasattr(model, 'model_performance'):
                    metrics[model_name] = model.model_performance
                else:
                    metrics[model_name] = {}
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    def cleanup_old_models(self, retention_days: int = None) -> Dict[str, Any]:
        """Clean up old model versions."""
        try:
            if retention_days is None:
                retention_days = SETTINGS.ml_model_retention_days
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cleaned_models = []
            
            # Clean up model files
            for model_name in self.models.keys():
                model_dir = os.path.join(SETTINGS.ml_model_storage_path, model_name)
                if os.path.exists(model_dir):
                    for filename in os.listdir(model_dir):
                        file_path = os.path.join(model_dir, filename)
                        if os.path.isfile(file_path):
                            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_time < cutoff_date:
                                os.remove(file_path)
                                cleaned_models.append(file_path)
            
            return {
                'status': 'success',
                'cleaned_files': cleaned_models,
                'retention_days': retention_days
            }
            
        except Exception as e:
            logger.error(f"Model cleanup failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def export_models(self, export_path: str) -> Dict[str, Any]:
        """Export all models to a specified path."""
        try:
            os.makedirs(export_path, exist_ok=True)
            exported_models = []
            
            for model_name, model in self.models.items():
                model_export_path = os.path.join(export_path, model_name)
                os.makedirs(model_export_path, exist_ok=True)
                
                if hasattr(model, 'save_models'):
                    success = model.save_models(model_export_path)
                    if success:
                        exported_models.append(model_name)
            
            return {
                'status': 'success',
                'exported_models': exported_models,
                'export_path': export_path
            }
            
        except Exception as e:
            logger.error(f"Model export failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def import_models(self, import_path: str) -> Dict[str, Any]:
        """Import models from a specified path."""
        try:
            imported_models = []
            
            for model_name, model in self.models.items():
                model_import_path = os.path.join(import_path, model_name)
                
                if os.path.exists(model_import_path):
                    if hasattr(model, 'load_models'):
                        success = model.load_models(model_import_path)
                        if success:
                            imported_models.append(model_name)
            
            return {
                'status': 'success',
                'imported_models': imported_models,
                'import_path': import_path
            }
            
        except Exception as e:
            logger.error(f"Model import failed: {e}")
            return {'status': 'failed', 'error': str(e)}
