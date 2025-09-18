"""Anomaly detection models for threat detection and behavioral analysis."""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import joblib
import os

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import DBSCAN
from pyod.models.iforest import IForest as PyODIForest
from pyod.models.lof import LOF
from pyod.models.ocsvm import OCSVM
from pyod.models.auto_encoder import AutoEncoder

from ..config import SETTINGS

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Advanced anomaly detection for threat detection and behavioral analysis."""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        self.model_performance = {}
        self.training_data = None
        self.is_trained = False
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize anomaly detection models."""
        self.models = {
            'isolation_forest': IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            ),
            'lof': LOF(contamination=0.1),
            'ocsvm': OCSVM(contamination=0.1),
            'auto_encoder': AutoEncoder(
                contamination=0.1,
                hidden_neurons=[64, 32, 16, 32, 64],
                epochs=100,
                batch_size=32
            ),
            'dbscan': DBSCAN(eps=0.5, min_samples=5)
        }
        
        # Initialize scalers and encoders
        self.scalers = {
            'standard': StandardScaler(),
            'robust': StandardScaler()
        }
        
        self.encoders = {
            'label': LabelEncoder()
        }
    
    async def train_models(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train all anomaly detection models."""
        try:
            logger.info("Starting anomaly detection model training...")
            
            # Store training data
            self.training_data = training_data.copy()
            
            # Prepare features
            features = self._prepare_features(training_data)
            
            # Train each model
            training_results = {}
            for model_name, model in self.models.items():
                try:
                    logger.info(f"Training {model_name}...")
                    
                    if model_name == 'dbscan':
                        # DBSCAN doesn't need training, just fit
                        model.fit(features)
                        training_results[model_name] = {
                            'status': 'success',
                            'n_clusters': len(set(model.labels_)) - (1 if -1 in model.labels_ else 0),
                            'n_noise': list(model.labels_).count(-1)
                        }
                    else:
                        # Train the model
                        model.fit(features)
                        training_results[model_name] = {'status': 'success'}
                    
                    # Calculate feature importance if available
                    if hasattr(model, 'feature_importances_'):
                        self.feature_importance[model_name] = model.feature_importances_
                    
                except Exception as e:
                    logger.error(f"Error training {model_name}: {e}")
                    training_results[model_name] = {'status': 'failed', 'error': str(e)}
            
            # Calculate overall performance
            self._calculate_model_performance(features)
            
            self.is_trained = True
            logger.info("Anomaly detection model training completed")
            
            return {
                'status': 'success',
                'models_trained': len([r for r in training_results.values() if r['status'] == 'success']),
                'training_results': training_results,
                'feature_importance': self.feature_importance,
                'model_performance': self.model_performance
            }
            
        except Exception as e:
            logger.error(f"Anomaly detection training failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def detect_anomalies(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in event data."""
        try:
            if not self.is_trained:
                return self._get_fallback_anomaly_detection(event_data)
            
            # Convert event to DataFrame
            event_df = pd.DataFrame([event_data])
            
            # Prepare features
            features = self._prepare_features(event_df)
            
            # Get predictions from all models
            anomaly_scores = {}
            anomaly_predictions = {}
            
            for model_name, model in self.models.items():
                try:
                    if model_name == 'dbscan':
                        # DBSCAN prediction
                        prediction = model.fit_predict(features)
                        is_anomaly = prediction[0] == -1
                        score = 1.0 if is_anomaly else 0.0
                    else:
                        # Other models
                        if hasattr(model, 'decision_function'):
                            score = model.decision_function(features)[0]
                            # Normalize score to 0-1 range
                            score = (score - score.min()) / (score.max() - score.min()) if score.max() != score.min() else 0.5
                        else:
                            score = model.score_samples(features)[0]
                            # Normalize score to 0-1 range
                            score = (score - score.min()) / (score.max() - score.min()) if score.max() != score.min() else 0.5
                        
                        is_anomaly = score > SETTINGS.anomaly_threshold
                    
                    anomaly_scores[model_name] = float(score)
                    anomaly_predictions[model_name] = bool(is_anomaly)
                    
                except Exception as e:
                    logger.error(f"Error in {model_name} prediction: {e}")
                    anomaly_scores[model_name] = 0.5
                    anomaly_predictions[model_name] = False
            
            # Ensemble prediction
            ensemble_score = np.mean(list(anomaly_scores.values()))
            ensemble_prediction = ensemble_score > SETTINGS.anomaly_threshold
            
            # Calculate confidence
            confidence = self._calculate_anomaly_confidence(anomaly_scores, anomaly_predictions)
            
            # Determine anomaly type
            anomaly_type = self._classify_anomaly_type(event_data, ensemble_score)
            
            return {
                'is_anomaly': bool(ensemble_prediction),
                'anomaly_score': float(ensemble_score),
                'confidence': confidence,
                'anomaly_type': anomaly_type,
                'model_scores': anomaly_scores,
                'model_predictions': anomaly_predictions,
                'feature_contributions': self._get_feature_contributions(event_data, features),
                'recommendations': self._get_anomaly_recommendations(anomaly_type, ensemble_score)
            }
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return self._get_fallback_anomaly_detection(event_data)
    
    async def detect_behavioral_anomalies(self, user_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect behavioral anomalies in user activity patterns."""
        try:
            if len(user_events) < SETTINGS.anomaly_min_samples:
                return {'is_anomaly': False, 'reason': 'Insufficient data for analysis'}
            
            # Convert to DataFrame
            events_df = pd.DataFrame(user_events)
            
            # Extract behavioral features
            behavioral_features = self._extract_behavioral_features(events_df)
            
            # Analyze patterns
            patterns = self._analyze_behavioral_patterns(behavioral_features)
            
            # Detect anomalies
            anomalies = self._detect_behavioral_anomalies(patterns)
            
            return {
                'is_anomaly': len(anomalies) > 0,
                'anomaly_count': len(anomalies),
                'anomalies': anomalies,
                'behavioral_patterns': patterns,
                'risk_level': self._assess_behavioral_risk(anomalies),
                'recommendations': self._get_behavioral_recommendations(anomalies)
            }
            
        except Exception as e:
            logger.error(f"Behavioral anomaly detection failed: {e}")
            return {'is_anomaly': False, 'error': str(e)}
    
    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features for anomaly detection."""
        try:
            # Select numeric features
            numeric_features = data.select_dtypes(include=[np.number]).columns.tolist()
            
            # Handle categorical features
            categorical_features = data.select_dtypes(include=['object']).columns.tolist()
            
            # Process numeric features
            if numeric_features:
                numeric_data = data[numeric_features].fillna(0)
                # Scale numeric features
                if 'standard' in self.scalers:
                    numeric_data = self.scalers['standard'].fit_transform(numeric_data)
            else:
                numeric_data = np.zeros((len(data), 1))
            
            # Process categorical features
            if categorical_features:
                categorical_data = data[categorical_features].fillna('unknown')
                # Encode categorical features
                encoded_data = []
                for col in categorical_features:
                    if col in self.encoders:
                        encoded_data.append(self.encoders[col].fit_transform(categorical_data[col]))
                    else:
                        # Create new encoder
                        encoder = LabelEncoder()
                        self.encoders[col] = encoder
                        encoded_data.append(encoder.fit_transform(categorical_data[col]))
                
                if encoded_data:
                    categorical_encoded = np.column_stack(encoded_data)
                else:
                    categorical_encoded = np.zeros((len(data), 1))
            else:
                categorical_encoded = np.zeros((len(data), 1))
            
            # Combine features
            features = np.column_stack([numeric_data, categorical_encoded])
            
            return features
            
        except Exception as e:
            logger.error(f"Feature preparation failed: {e}")
            return np.zeros((len(data), 1))
    
    def _extract_behavioral_features(self, events_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract behavioral features from user events."""
        features = {}
        
        try:
            # Time-based features
            if 'timestamp' in events_df.columns:
                events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
                features['hour_of_day'] = events_df['timestamp'].dt.hour.tolist()
                features['day_of_week'] = events_df['timestamp'].dt.dayofweek.tolist()
                features['is_weekend'] = (events_df['timestamp'].dt.dayofweek >= 5).tolist()
            
            # Event frequency features
            features['total_events'] = len(events_df)
            features['unique_event_types'] = events_df['event_type'].nunique() if 'event_type' in events_df.columns else 0
            features['unique_sources'] = events_df['source'].nunique() if 'source' in events_df.columns else 0
            
            # Severity distribution
            if 'severity' in events_df.columns:
                severity_counts = events_df['severity'].value_counts()
                features['high_severity_ratio'] = severity_counts.get('HIGH', 0) / len(events_df)
                features['critical_severity_ratio'] = severity_counts.get('CRITICAL', 0) / len(events_df)
            
            # IP-based features
            if 'ip' in events_df.columns:
                features['unique_ips'] = events_df['ip'].nunique()
                features['internal_ip_ratio'] = events_df['ip'].str.startswith(('10.', '192.168.', '172.')).sum() / len(events_df)
            
            return features
            
        except Exception as e:
            logger.error(f"Behavioral feature extraction failed: {e}")
            return {}
    
    def _analyze_behavioral_patterns(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze behavioral patterns for anomalies."""
        patterns = {}
        
        try:
            # Time pattern analysis
            if 'hour_of_day' in features:
                hour_dist = np.bincount(features['hour_of_day'], minlength=24)
                patterns['peak_hours'] = np.argmax(hour_dist)
                patterns['off_hours_activity'] = np.sum(hour_dist[[0, 1, 2, 3, 4, 5, 22, 23]]) / np.sum(hour_dist)
            
            # Event pattern analysis
            if 'total_events' in features:
                patterns['event_volume'] = features['total_events']
                patterns['event_diversity'] = features.get('unique_event_types', 0) / max(features['total_events'], 1)
            
            # Risk pattern analysis
            if 'high_severity_ratio' in features:
                patterns['risk_level'] = features['high_severity_ratio'] + features.get('critical_severity_ratio', 0)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Behavioral pattern analysis failed: {e}")
            return {}
    
    def _detect_behavioral_anomalies(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect behavioral anomalies from patterns."""
        anomalies = []
        
        try:
            # Off-hours activity anomaly
            if patterns.get('off_hours_activity', 0) > 0.3:
                anomalies.append({
                    'type': 'off_hours_activity',
                    'severity': 'MEDIUM',
                    'description': 'High activity during off-hours',
                    'value': patterns['off_hours_activity']
                })
            
            # High event volume anomaly
            if patterns.get('event_volume', 0) > 1000:
                anomalies.append({
                    'type': 'high_event_volume',
                    'severity': 'HIGH',
                    'description': 'Unusually high event volume',
                    'value': patterns['event_volume']
                })
            
            # High risk level anomaly
            if patterns.get('risk_level', 0) > 0.5:
                anomalies.append({
                    'type': 'high_risk_level',
                    'severity': 'CRITICAL',
                    'description': 'High proportion of high/critical severity events',
                    'value': patterns['risk_level']
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Behavioral anomaly detection failed: {e}")
            return []
    
    def _assess_behavioral_risk(self, anomalies: List[Dict[str, Any]]) -> str:
        """Assess overall behavioral risk level."""
        if not anomalies:
            return 'LOW'
        
        critical_count = len([a for a in anomalies if a.get('severity') == 'CRITICAL'])
        high_count = len([a for a in anomalies if a.get('severity') == 'HIGH'])
        
        if critical_count > 0:
            return 'CRITICAL'
        elif high_count > 1:
            return 'HIGH'
        elif high_count > 0 or len(anomalies) > 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_behavioral_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Get recommendations for behavioral anomalies."""
        recommendations = []
        
        for anomaly in anomalies:
            if anomaly['type'] == 'off_hours_activity':
                recommendations.append("Review user access patterns and implement time-based restrictions")
            elif anomaly['type'] == 'high_event_volume':
                recommendations.append("Investigate potential automated attacks or system issues")
            elif anomaly['type'] == 'high_risk_level':
                recommendations.append("Immediately investigate high-risk events and consider user suspension")
        
        return recommendations
    
    def _calculate_anomaly_confidence(self, scores: Dict[str, float], predictions: Dict[str, bool]) -> float:
        """Calculate confidence in anomaly detection."""
        try:
            # Calculate agreement between models
            prediction_agreement = sum(predictions.values()) / len(predictions)
            
            # Calculate score consistency
            score_std = np.std(list(scores.values()))
            score_consistency = 1.0 / (1.0 + score_std)
            
            # Combine factors
            confidence = (prediction_agreement * 0.6) + (score_consistency * 0.4)
            
            return float(confidence)
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5
    
    def _classify_anomaly_type(self, event_data: Dict[str, Any], score: float) -> str:
        """Classify the type of anomaly."""
        try:
            event_type = event_data.get('event_type', '').lower()
            source = event_data.get('source', '').lower()
            severity = event_data.get('severity', '').upper()
            
            # High score anomalies
            if score > 0.8:
                if 'login' in event_type or 'auth' in event_type:
                    return 'Authentication Anomaly'
                elif 'network' in event_type or 'connection' in event_type:
                    return 'Network Anomaly'
                elif 'file' in event_type or 'access' in event_type:
                    return 'Data Access Anomaly'
                else:
                    return 'System Anomaly'
            
            # Medium score anomalies
            elif score > 0.6:
                return 'Behavioral Anomaly'
            
            # Low score anomalies
            else:
                return 'Minor Anomaly'
                
        except Exception as e:
            logger.error(f"Anomaly type classification failed: {e}")
            return 'Unknown Anomaly'
    
    def _get_feature_contributions(self, event_data: Dict[str, Any], features: np.ndarray) -> Dict[str, float]:
        """Get feature contributions to anomaly score."""
        try:
            # Simple feature importance based on variance
            feature_importance = np.var(features, axis=0)
            feature_names = [f"feature_{i}" for i in range(len(feature_importance))]
            
            return dict(zip(feature_names, feature_importance.tolist()))
            
        except Exception as e:
            logger.error(f"Feature contribution calculation failed: {e}")
            return {}
    
    def _get_anomaly_recommendations(self, anomaly_type: str, score: float) -> List[str]:
        """Get recommendations based on anomaly type and score."""
        recommendations = []
        
        if score > 0.8:
            recommendations.extend([
                "Immediately investigate this event",
                "Consider blocking the source IP",
                "Review related events for patterns"
            ])
        elif score > 0.6:
            recommendations.extend([
                "Monitor this event closely",
                "Check for similar patterns in recent events",
                "Consider additional logging"
            ])
        else:
            recommendations.append("Continue monitoring for pattern development")
        
        # Type-specific recommendations
        if 'Authentication' in anomaly_type:
            recommendations.append("Review user authentication logs")
        elif 'Network' in anomaly_type:
            recommendations.append("Check network security controls")
        elif 'Data Access' in anomaly_type:
            recommendations.append("Review data access permissions")
        
        return recommendations
    
    def _calculate_model_performance(self, features: np.ndarray):
        """Calculate model performance metrics."""
        try:
            # This would typically use cross-validation
            # For now, we'll use simple metrics
            self.model_performance = {
                'training_samples': len(features),
                'feature_count': features.shape[1],
                'last_training': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance calculation failed: {e}")
            self.model_performance = {}
    
    def _get_fallback_anomaly_detection(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback anomaly detection when models are not trained."""
        return {
            'is_anomaly': False,
            'anomaly_score': 0.5,
            'confidence': 0.3,
            'anomaly_type': 'Unknown',
            'model_scores': {},
            'model_predictions': {},
            'feature_contributions': {},
            'recommendations': ['Models not trained - manual review required']
        }
    
    def save_models(self, path: str = None) -> bool:
        """Save trained models to disk."""
        try:
            if not self.is_trained:
                logger.warning("No trained models to save")
                return False
            
            save_path = path or SETTINGS.ml_model_storage_path
            os.makedirs(save_path, exist_ok=True)
            
            # Save models
            for model_name, model in self.models.items():
                model_path = os.path.join(save_path, f"{model_name}_anomaly_model.joblib")
                joblib.dump(model, model_path)
            
            # Save scalers and encoders
            scaler_path = os.path.join(save_path, "anomaly_scalers.joblib")
            joblib.dump(self.scalers, scaler_path)
            
            encoder_path = os.path.join(save_path, "anomaly_encoders.joblib")
            joblib.dump(self.encoders, encoder_path)
            
            logger.info(f"Anomaly detection models saved to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
            return False
    
    def load_models(self, path: str = None) -> bool:
        """Load trained models from disk."""
        try:
            load_path = path or SETTINGS.ml_model_storage_path
            
            # Load models
            for model_name in self.models.keys():
                model_path = os.path.join(load_path, f"{model_name}_anomaly_model.joblib")
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
            
            # Load scalers and encoders
            scaler_path = os.path.join(load_path, "anomaly_scalers.joblib")
            if os.path.exists(scaler_path):
                self.scalers = joblib.load(scaler_path)
            
            encoder_path = os.path.join(load_path, "anomaly_encoders.joblib")
            if os.path.exists(encoder_path):
                self.encoders = joblib.load(encoder_path)
            
            self.is_trained = True
            logger.info(f"Anomaly detection models loaded from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
