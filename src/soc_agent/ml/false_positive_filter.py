"""ML-based false positive reduction and filtering system."""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import joblib
import os
import json

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_curve
from sklearn.feature_extraction.text import TfidfVectorizer
import xgboost as xgb
import lightgbm as lgb

from ..config import SETTINGS

logger = logging.getLogger(__name__)


class FalsePositiveFilter:
    """ML-based false positive reduction and filtering system."""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.vectorizers = {}
        self.feature_importance = {}
        self.model_performance = {}
        self.feedback_data = []
        self.is_trained = False
        
        # False positive patterns
        self.fp_patterns = {
            'benign_activities': [
                'scheduled_task', 'backup', 'maintenance', 'update', 'scan',
                'health_check', 'monitoring', 'log_rotation', 'cleanup'
            ],
            'normal_network_traffic': [
                'dns_query', 'ntp_sync', 'dhcp_request', 'arp_request',
                'icmp_ping', 'tcp_handshake', 'udp_query'
            ],
            'legitimate_errors': [
                'connection_timeout', 'service_unavailable', 'temporary_failure',
                'rate_limit_exceeded', 'authentication_failed'
            ],
            'system_noise': [
                'debug_message', 'info_log', 'warning_log', 'verbose_log',
                'trace_log', 'audit_log'
            ]
        }
        
        # True positive patterns
        self.tp_patterns = {
            'malicious_activities': [
                'malware', 'virus', 'trojan', 'rootkit', 'backdoor',
                'ransomware', 'botnet', 'command_control'
            ],
            'attack_indicators': [
                'exploit', 'injection', 'brute_force', 'privilege_escalation',
                'lateral_movement', 'data_exfiltration', 'persistence'
            ],
            'suspicious_behavior': [
                'unusual_access', 'off_hours_activity', 'privilege_abuse',
                'data_breach', 'unauthorized_access', 'anomalous_traffic'
            ]
        }
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize false positive filtering models."""
        self.models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1,
                class_weight='balanced'
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            ),
            'logistic_regression': LogisticRegression(
                max_iter=1000,
                random_state=42,
                n_jobs=-1,
                class_weight='balanced'
            ),
            'svm': SVC(
                kernel='rbf',
                probability=True,
                random_state=42,
                class_weight='balanced'
            ),
            'naive_bayes': MultinomialNB(),
            'xgboost': xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
                scale_pos_weight=2  # Weight positive class more
            ),
            'lightgbm': lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
                verbose=-1,
                class_weight='balanced'
            )
        }
        
        # Create ensemble model
        self.models['ensemble'] = VotingClassifier([
            ('rf', self.models['random_forest']),
            ('gb', self.models['gradient_boosting']),
            ('lr', self.models['logistic_regression']),
            ('xgb', self.models['xgboost']),
            ('lgb', self.models['lightgbm'])
        ])
        
        # Initialize scalers and encoders
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': StandardScaler()
        }
        
        self.encoders = {
            'label': LabelEncoder()
        }
        
        # Initialize text vectorizers
        self.vectorizers = {
            'tfidf': TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 3)
            )
        }
    
    async def train_models(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train false positive filtering models."""
        try:
            logger.info("Starting false positive filter model training...")
            
            # Prepare features and target
            X, y = self._prepare_training_data(training_data)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scalers['standard'].fit_transform(X_train)
            X_test_scaled = self.scalers['standard'].transform(X_test)
            
            # Train each model
            training_results = {}
            for model_name, model in self.models.items():
                try:
                    logger.info(f"Training {model_name}...")
                    
                    # Train model
                    model.fit(X_train_scaled, y_train)
                    
                    # Make predictions
                    y_pred = model.predict(X_test_scaled)
                    y_pred_proba = model.predict_proba(X_test_scaled)
                    
                    # Calculate metrics
                    accuracy = accuracy_score(y_test, y_pred)
                    precision = precision_recall_curve(y_test, y_pred_proba[:, 1])
                    
                    # Cross-validation score
                    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='accuracy')
                    
                    # Classification report
                    class_report = classification_report(y_test, y_pred, output_dict=True)
                    
                    # Confusion matrix
                    conf_matrix = confusion_matrix(y_test, y_pred)
                    
                    training_results[model_name] = {
                        'status': 'success',
                        'accuracy': float(accuracy),
                        'precision': float(precision[0][-1]),
                        'recall': float(precision[1][-1]),
                        'f1_score': float(class_report['1']['f1-score']),
                        'cv_mean': float(cv_scores.mean()),
                        'cv_std': float(cv_scores.std()),
                        'classification_report': class_report,
                        'confusion_matrix': conf_matrix.tolist()
                    }
                    
                    # Store feature importance
                    if hasattr(model, 'feature_importances_'):
                        self.feature_importance[model_name] = model.feature_importances_.tolist()
                    elif hasattr(model, 'estimators_'):
                        # For ensemble models
                        importances = []
                        for estimator in model.estimators_:
                            if hasattr(estimator, 'feature_importances_'):
                                importances.append(estimator.feature_importances_)
                        if importances:
                            self.feature_importance[model_name] = np.mean(importances, axis=0).tolist()
                    
                except Exception as e:
                    logger.error(f"Error training {model_name}: {e}")
                    training_results[model_name] = {'status': 'failed', 'error': str(e)}
            
            # Calculate overall performance
            self._calculate_model_performance(X, y)
            
            self.is_trained = True
            logger.info("False positive filter model training completed")
            
            return {
                'status': 'success',
                'models_trained': len([r for r in training_results.values() if r['status'] == 'success']),
                'training_results': training_results,
                'feature_importance': self.feature_importance,
                'model_performance': self.model_performance
            }
            
        except Exception as e:
            logger.error(f"False positive filter training failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def filter_false_positives(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter false positives from alert data."""
        try:
            if not self.is_trained:
                return self._get_fallback_filtering(alert_data)
            
            # Prepare features
            features = self._prepare_features(alert_data)
            features_scaled = self.scalers['standard'].transform([features])
            
            # Get predictions from all models
            predictions = {}
            probabilities = {}
            
            for model_name, model in self.models.items():
                try:
                    # Make prediction
                    pred = model.predict(features_scaled)[0]
                    proba = model.predict_proba(features_scaled)[0]
                    
                    predictions[model_name] = int(pred)
                    probabilities[model_name] = proba.tolist()
                    
                except Exception as e:
                    logger.error(f"Error in {model_name} prediction: {e}")
                    predictions[model_name] = 0
                    probabilities[model_name] = [0.5, 0.5]
            
            # Calculate ensemble prediction
            ensemble_pred = max(set(predictions.values()), key=list(predictions.values()).count)
            ensemble_proba = np.mean([probs[1] for probs in probabilities.values()])
            
            # Determine if it's a false positive
            is_false_positive = ensemble_pred == 0
            confidence = ensemble_proba if not is_false_positive else 1.0 - ensemble_proba
            
            # Check confidence threshold
            if confidence < SETTINGS.fp_model_confidence_threshold:
                is_false_positive = False  # Low confidence, treat as true positive
            
            # Get filtering reason
            filtering_reason = self._get_filtering_reason(alert_data, is_false_positive, confidence)
            
            # Generate recommendations
            recommendations = self._generate_filtering_recommendations(
                is_false_positive, confidence, filtering_reason
            )
            
            return {
                'is_false_positive': bool(is_false_positive),
                'confidence': float(confidence),
                'filtering_reason': filtering_reason,
                'model_predictions': predictions,
                'model_probabilities': probabilities,
                'recommendations': recommendations,
                'filtering_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"False positive filtering failed: {e}")
            return self._get_fallback_filtering(alert_data)
    
    async def batch_filter_false_positives(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter false positives from multiple alerts in batch."""
        try:
            results = []
            
            for alert in alerts:
                filtering_result = await self.filter_false_positives(alert)
                results.append({
                    'alert_id': alert.get('id', 'unknown'),
                    'filtering_result': filtering_result
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Batch false positive filtering failed: {e}")
            return []
    
    async def learn_from_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from analyst feedback to improve filtering."""
        try:
            if not SETTINGS.fp_learning_enabled:
                return {'status': 'disabled', 'message': 'FP learning is disabled'}
            
            # Store feedback data
            self.feedback_data.append({
                'alert_data': feedback_data.get('alert_data', {}),
                'is_false_positive': feedback_data.get('is_false_positive', False),
                'analyst_confidence': feedback_data.get('analyst_confidence', 1.0),
                'feedback_timestamp': datetime.now().isoformat()
            })
            
            # Retrain models if we have enough feedback
            if len(self.feedback_data) >= 100:
                logger.info("Retraining models with feedback data...")
                
                # Convert feedback to training data
                feedback_df = pd.DataFrame(self.feedback_data)
                feedback_df['is_false_positive'] = feedback_df['is_false_positive'].astype(int)
                
                # Retrain models
                retrain_result = await self.train_models(feedback_df)
                
                return {
                    'status': 'success',
                    'message': 'Models retrained with feedback data',
                    'feedback_count': len(self.feedback_data),
                    'retrain_result': retrain_result
                }
            else:
                return {
                    'status': 'success',
                    'message': f'Feedback stored. Need {100 - len(self.feedback_data)} more samples for retraining',
                    'feedback_count': len(self.feedback_data)
                }
            
        except Exception as e:
            logger.error(f"Feedback learning failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _prepare_training_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for false positive filtering."""
        try:
            features = []
            labels = []
            
            for _, row in data.iterrows():
                # Prepare feature vector
                feature_vector = self._extract_features(row.to_dict())
                features.append(feature_vector)
                
                # Extract label (0 = false positive, 1 = true positive)
                is_false_positive = row.get('is_false_positive', False)
                labels.append(1 if is_false_positive else 0)
            
            return np.array(features), np.array(labels)
            
        except Exception as e:
            logger.error(f"Training data preparation failed: {e}")
            return np.array([]), np.array([])
    
    def _prepare_features(self, alert_data: Dict[str, Any]) -> np.ndarray:
        """Prepare features for false positive filtering."""
        try:
            features = []
            
            # Text features
            message = alert_data.get('message', '')
            event_type = alert_data.get('event_type', '')
            source = alert_data.get('source', '')
            
            # Combine text fields
            combined_text = f"{message} {event_type} {source}"
            
            # Extract text features using TF-IDF
            if 'tfidf' in self.vectorizers and hasattr(self.vectorizers['tfidf'], 'vocabulary_'):
                text_features = self.vectorizers['tfidf'].transform([combined_text]).toarray()[0]
                features.extend(text_features)
            else:
                # Fallback text features
                features.extend([
                    len(message),
                    len(event_type),
                    len(source),
                    message.count('error'),
                    message.count('failed'),
                    message.count('success'),
                    message.count('warning'),
                    message.count('info'),
                    message.count('debug')
                ])
            
            # Pattern matching features
            fp_score = self._calculate_fp_pattern_score(combined_text)
            tp_score = self._calculate_tp_pattern_score(combined_text)
            features.extend([fp_score, tp_score])
            
            # Numeric features
            features.extend([
                alert_data.get('severity_score', 50) / 100.0,
                alert_data.get('confidence_score', 50) / 100.0,
                alert_data.get('anomaly_score', 0.5),
                alert_data.get('risk_score', 50) / 100.0,
                alert_data.get('threat_count', 1) / 10.0,
                alert_data.get('user_count', 1) / 100.0,
                alert_data.get('ip_count', 1) / 100.0,
                alert_data.get('port_count', 1) / 100.0
            ])
            
            # Categorical features
            features.extend([
                1 if alert_data.get('is_internal', False) else 0,
                1 if alert_data.get('is_privileged', False) else 0,
                1 if alert_data.get('is_encrypted', False) else 0,
                1 if alert_data.get('has_malware', False) else 0,
                1 if alert_data.get('has_exploit', False) else 0,
                1 if alert_data.get('has_data_access', False) else 0,
                1 if alert_data.get('is_scheduled', False) else 0,
                1 if alert_data.get('is_maintenance', False) else 0
            ])
            
            # Time-based features
            timestamp = alert_data.get('timestamp', datetime.now().isoformat())
            try:
                dt = pd.to_datetime(timestamp)
                features.extend([
                    dt.hour / 24.0,
                    dt.dayofweek / 7.0,
                    dt.month / 12.0,
                    1 if dt.hour < 6 or dt.hour > 22 else 0,  # Off-hours
                    1 if dt.dayofweek >= 5 else 0  # Weekend
                ])
            except:
                features.extend([0.5, 0.5, 0.5, 0, 0])
            
            # Network features
            ip = alert_data.get('ip', '')
            features.extend([
                1 if ip.startswith(('10.', '192.168.', '172.')) else 0,  # Internal IP
                1 if ip.startswith(('127.', 'localhost')) else 0,  # Localhost
                len(ip.split('.')) if '.' in ip else 0,  # IP format
                1 if ip == '0.0.0.0' else 0  # Invalid IP
            ])
            
            # Frequency features
            features.extend([
                alert_data.get('alert_frequency', 1) / 100.0,
                alert_data.get('source_frequency', 1) / 100.0,
                alert_data.get('user_frequency', 1) / 100.0,
                alert_data.get('ip_frequency', 1) / 100.0
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Feature preparation failed: {e}")
            return np.zeros(50)  # Return default feature vector
    
    def _extract_features(self, alert_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from alert data for training."""
        return self._prepare_features(alert_data)
    
    def _calculate_fp_pattern_score(self, text: str) -> float:
        """Calculate false positive pattern score."""
        try:
            text_lower = text.lower()
            fp_score = 0.0
            
            for category, patterns in self.fp_patterns.items():
                for pattern in patterns:
                    if pattern in text_lower:
                        fp_score += 1.0
            
            # Normalize score
            total_patterns = sum(len(patterns) for patterns in self.fp_patterns.values())
            return fp_score / total_patterns if total_patterns > 0 else 0.0
            
        except Exception as e:
            logger.error(f"FP pattern score calculation failed: {e}")
            return 0.0
    
    def _calculate_tp_pattern_score(self, text: str) -> float:
        """Calculate true positive pattern score."""
        try:
            text_lower = text.lower()
            tp_score = 0.0
            
            for category, patterns in self.tp_patterns.items():
                for pattern in patterns:
                    if pattern in text_lower:
                        tp_score += 1.0
            
            # Normalize score
            total_patterns = sum(len(patterns) for patterns in self.tp_patterns.values())
            return tp_score / total_patterns if total_patterns > 0 else 0.0
            
        except Exception as e:
            logger.error(f"TP pattern score calculation failed: {e}")
            return 0.0
    
    def _get_filtering_reason(self, alert_data: Dict[str, Any], is_false_positive: bool, confidence: float) -> str:
        """Get reason for filtering decision."""
        try:
            if not is_false_positive:
                return "Alert appears to be a true positive based on analysis"
            
            message = alert_data.get('message', '').lower()
            event_type = alert_data.get('event_type', '').lower()
            source = alert_data.get('source', '').lower()
            
            # Check for specific false positive patterns
            if any(pattern in message for pattern in self.fp_patterns['benign_activities']):
                return "Alert matches benign activity patterns"
            elif any(pattern in message for pattern in self.fp_patterns['normal_network_traffic']):
                return "Alert matches normal network traffic patterns"
            elif any(pattern in message for pattern in self.fp_patterns['legitimate_errors']):
                return "Alert matches legitimate error patterns"
            elif any(pattern in message for pattern in self.fp_patterns['system_noise']):
                return "Alert matches system noise patterns"
            elif alert_data.get('is_scheduled', False):
                return "Alert is from scheduled activity"
            elif alert_data.get('is_maintenance', False):
                return "Alert is from maintenance activity"
            elif confidence < 0.3:
                return "Low confidence in alert validity"
            else:
                return "Alert matches false positive patterns"
                
        except Exception as e:
            logger.error(f"Filtering reason calculation failed: {e}")
            return "Unable to determine filtering reason"
    
    def _generate_filtering_recommendations(
        self, 
        is_false_positive: bool, 
        confidence: float, 
        filtering_reason: str
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on filtering decision."""
        recommendations = []
        
        if is_false_positive:
            if confidence > 0.8:
                recommendations.append({
                    'action': 'Suppress alert',
                    'description': 'High confidence false positive - suppress this alert',
                    'priority': 'HIGH'
                })
            else:
                recommendations.append({
                    'action': 'Review alert',
                    'description': 'Medium confidence false positive - manual review recommended',
                    'priority': 'MEDIUM'
                })
            
            # Pattern-specific recommendations
            if 'benign activity' in filtering_reason:
                recommendations.append({
                    'action': 'Update whitelist',
                    'description': 'Consider adding to whitelist for future alerts',
                    'priority': 'LOW'
                })
            elif 'scheduled activity' in filtering_reason:
                recommendations.append({
                    'action': 'Schedule exception',
                    'description': 'Create scheduled exception for this activity',
                    'priority': 'LOW'
                })
        else:
            if confidence > 0.8:
                recommendations.append({
                    'action': 'Investigate immediately',
                    'description': 'High confidence true positive - investigate immediately',
                    'priority': 'HIGH'
                })
            else:
                recommendations.append({
                    'action': 'Monitor closely',
                    'description': 'Medium confidence true positive - monitor closely',
                    'priority': 'MEDIUM'
                })
        
        return recommendations
    
    def _calculate_model_performance(self, X: np.ndarray, y: np.ndarray):
        """Calculate model performance metrics."""
        try:
            self.model_performance = {
                'training_samples': len(X),
                'feature_count': X.shape[1],
                'false_positive_count': int(np.sum(y == 0)),
                'true_positive_count': int(np.sum(y == 1)),
                'class_balance': float(np.sum(y == 1) / len(y)),
                'last_training': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance calculation failed: {e}")
            self.model_performance = {}
    
    def _get_fallback_filtering(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback filtering when models are not trained."""
        # Simple rule-based filtering
        message = alert_data.get('message', '').lower()
        
        # Check for obvious false positive patterns
        is_false_positive = any(
            pattern in message for pattern in [
                'scheduled', 'backup', 'maintenance', 'update', 'scan',
                'health_check', 'monitoring', 'log_rotation', 'cleanup'
            ]
        )
        
        return {
            'is_false_positive': is_false_positive,
            'confidence': 0.3,
            'filtering_reason': 'Rule-based filtering (models not trained)',
            'model_predictions': {},
            'model_probabilities': {},
            'recommendations': [{'action': 'Manual review', 'description': 'Models not trained - manual review required', 'priority': 'LOW'}],
            'filtering_timestamp': datetime.now().isoformat()
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
                model_path = os.path.join(save_path, f"{model_name}_fp_filter.joblib")
                joblib.dump(model, model_path)
            
            # Save scalers and encoders
            scaler_path = os.path.join(save_path, "fp_filter_scalers.joblib")
            joblib.dump(self.scalers, scaler_path)
            
            encoder_path = os.path.join(save_path, "fp_filter_encoders.joblib")
            joblib.dump(self.encoders, encoder_path)
            
            # Save vectorizers
            vectorizer_path = os.path.join(save_path, "fp_filter_vectorizers.joblib")
            joblib.dump(self.vectorizers, vectorizer_path)
            
            # Save feature importance
            importance_path = os.path.join(save_path, "fp_filter_feature_importance.json")
            with open(importance_path, 'w') as f:
                json.dump(self.feature_importance, f)
            
            # Save feedback data
            feedback_path = os.path.join(save_path, "fp_filter_feedback.json")
            with open(feedback_path, 'w') as f:
                json.dump(self.feedback_data, f)
            
            logger.info(f"False positive filter models saved to {save_path}")
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
                model_path = os.path.join(load_path, f"{model_name}_fp_filter.joblib")
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
            
            # Load scalers and encoders
            scaler_path = os.path.join(load_path, "fp_filter_scalers.joblib")
            if os.path.exists(scaler_path):
                self.scalers = joblib.load(scaler_path)
            
            encoder_path = os.path.join(load_path, "fp_filter_encoders.joblib")
            if os.path.exists(encoder_path):
                self.encoders = joblib.load(encoder_path)
            
            # Load vectorizers
            vectorizer_path = os.path.join(load_path, "fp_filter_vectorizers.joblib")
            if os.path.exists(vectorizer_path):
                self.vectorizers = joblib.load(vectorizer_path)
            
            # Load feature importance
            importance_path = os.path.join(load_path, "fp_filter_feature_importance.json")
            if os.path.exists(importance_path):
                with open(importance_path, 'r') as f:
                    self.feature_importance = json.load(f)
            
            # Load feedback data
            feedback_path = os.path.join(load_path, "fp_filter_feedback.json")
            if os.path.exists(feedback_path):
                with open(feedback_path, 'r') as f:
                    self.feedback_data = json.load(f)
            
            self.is_trained = True
            logger.info(f"False positive filter models loaded from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
