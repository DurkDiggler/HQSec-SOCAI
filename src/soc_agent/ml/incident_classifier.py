"""Automated incident classification and categorization system."""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import joblib
import os
import json

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import StandardScaler, LabelEncoder, MultiLabelBinarizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
import xgboost as xgb
import lightgbm as lgb

from ..config import SETTINGS

logger = logging.getLogger(__name__)


class IncidentClassifier:
    """Automated incident classification and categorization system."""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.vectorizers = {}
        self.class_labels = []
        self.feature_importance = {}
        self.model_performance = {}
        self.is_trained = False
        
        # Incident categories
        self.incident_categories = {
            'malware': {
                'keywords': ['virus', 'malware', 'trojan', 'worm', 'rootkit', 'backdoor', 'ransomware'],
                'description': 'Malware-related incidents'
            },
            'intrusion': {
                'keywords': ['intrusion', 'breach', 'unauthorized', 'access', 'penetration', 'hack'],
                'description': 'Unauthorized access incidents'
            },
            'data_breach': {
                'keywords': ['data', 'breach', 'leak', 'exfiltration', 'stolen', 'exposed'],
                'description': 'Data breach incidents'
            },
            'ddos': {
                'keywords': ['ddos', 'dos', 'denial', 'service', 'flood', 'overload'],
                'description': 'Denial of service attacks'
            },
            'phishing': {
                'keywords': ['phishing', 'email', 'spoof', 'fake', 'scam', 'social'],
                'description': 'Phishing and social engineering'
            },
            'insider_threat': {
                'keywords': ['insider', 'employee', 'internal', 'privilege', 'abuse'],
                'description': 'Insider threat incidents'
            },
            'vulnerability': {
                'keywords': ['vulnerability', 'exploit', 'patch', 'cve', 'weakness'],
                'description': 'Vulnerability exploitation'
            },
            'network_attack': {
                'keywords': ['network', 'port', 'scan', 'sniff', 'man-in-the-middle'],
                'description': 'Network-based attacks'
            },
            'web_attack': {
                'keywords': ['web', 'sql', 'injection', 'xss', 'csrf', 'website'],
                'description': 'Web application attacks'
            },
            'system_compromise': {
                'keywords': ['system', 'server', 'host', 'compromise', 'root', 'admin'],
                'description': 'System compromise incidents'
            }
        }
        
        # Severity levels
        self.severity_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        
        # Priority levels
        self.priority_levels = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize classification models."""
        self.models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
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
                n_jobs=-1
            ),
            'svm': SVC(
                kernel='rbf',
                probability=True,
                random_state=42
            ),
            'naive_bayes': MultinomialNB(),
            'xgboost': xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            ),
            'lightgbm': lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
                verbose=-1
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
            'category': LabelEncoder(),
            'severity': LabelEncoder(),
            'priority': LabelEncoder()
        }
        
        # Initialize text vectorizers
        self.vectorizers = {
            'tfidf': TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            ),
            'count': CountVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
        }
    
    async def train_models(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train incident classification models."""
        try:
            logger.info("Starting incident classification model training...")
            
            # Prepare features and targets
            X, y_category, y_severity, y_priority = self._prepare_training_data(training_data)
            
            # Split data
            X_train, X_test, y_cat_train, y_cat_test, y_sev_train, y_sev_test, y_pri_train, y_pri_test = train_test_split(
                X, y_category, y_severity, y_priority, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scalers['standard'].fit_transform(X_train)
            X_test_scaled = self.scalers['standard'].transform(X_test)
            
            # Train models for each classification task
            training_results = {}
            
            # Category classification
            category_results = await self._train_classification_models(
                'category', X_train_scaled, X_test_scaled, y_cat_train, y_cat_test
            )
            training_results['category'] = category_results
            
            # Severity classification
            severity_results = await self._train_classification_models(
                'severity', X_train_scaled, X_test_scaled, y_sev_train, y_sev_test
            )
            training_results['severity'] = severity_results
            
            # Priority classification
            priority_results = await self._train_classification_models(
                'priority', X_train_scaled, X_test_scaled, y_pri_train, y_pri_test
            )
            training_results['priority'] = priority_results
            
            # Calculate overall performance
            self._calculate_model_performance(X, y_category, y_severity, y_priority)
            
            self.is_trained = True
            logger.info("Incident classification model training completed")
            
            return {
                'status': 'success',
                'training_results': training_results,
                'feature_importance': self.feature_importance,
                'model_performance': self.model_performance,
                'class_labels': {
                    'categories': self.class_labels,
                    'severity_levels': self.severity_levels,
                    'priority_levels': self.priority_levels
                }
            }
            
        except Exception as e:
            logger.error(f"Incident classification training failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _train_classification_models(
        self, 
        task_name: str, 
        X_train: np.ndarray, 
        X_test: np.ndarray, 
        y_train: np.ndarray, 
        y_test: np.ndarray
    ) -> Dict[str, Any]:
        """Train classification models for a specific task."""
        results = {}
        
        for model_name, model in self.models.items():
            try:
                logger.info(f"Training {model_name} for {task_name}...")
                
                # Train model
                model.fit(X_train, y_train)
                
                # Make predictions
                y_pred = model.predict(X_test)
                y_pred_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None
                
                # Calculate metrics
                accuracy = accuracy_score(y_test, y_pred)
                
                # Cross-validation score
                cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
                
                # Classification report
                class_report = classification_report(y_test, y_pred, output_dict=True)
                
                # Confusion matrix
                conf_matrix = confusion_matrix(y_test, y_pred)
                
                results[model_name] = {
                    'status': 'success',
                    'accuracy': float(accuracy),
                    'cv_mean': float(cv_scores.mean()),
                    'cv_std': float(cv_scores.std()),
                    'classification_report': class_report,
                    'confusion_matrix': conf_matrix.tolist()
                }
                
                # Store feature importance
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[f"{task_name}_{model_name}"] = model.feature_importances_.tolist()
                elif hasattr(model, 'estimators_'):
                    # For ensemble models
                    importances = []
                    for estimator in model.estimators_:
                        if hasattr(estimator, 'feature_importances_'):
                            importances.append(estimator.feature_importances_)
                    if importances:
                        self.feature_importance[f"{task_name}_{model_name}"] = np.mean(importances, axis=0).tolist()
                
            except Exception as e:
                logger.error(f"Error training {model_name} for {task_name}: {e}")
                results[model_name] = {'status': 'failed', 'error': str(e)}
        
        return results
    
    async def classify_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify an incident into categories, severity, and priority."""
        try:
            if not self.is_trained:
                return self._get_fallback_classification(incident_data)
            
            # Prepare features
            features = self._prepare_features(incident_data)
            features_scaled = self.scalers['standard'].transform([features])
            
            # Get predictions from all models
            predictions = {}
            probabilities = {}
            
            for task_name in ['category', 'severity', 'priority']:
                task_predictions = {}
                task_probabilities = {}
                
                for model_name, model in self.models.items():
                    try:
                        # Get model for this task
                        task_model = getattr(self, f"{task_name}_model", model)
                        
                        # Make prediction
                        pred = task_model.predict(features_scaled)[0]
                        proba = task_model.predict_proba(features_scaled)[0] if hasattr(task_model, 'predict_proba') else None
                        
                        task_predictions[model_name] = pred
                        if proba is not None:
                            task_probabilities[model_name] = proba.tolist()
                        
                    except Exception as e:
                        logger.error(f"Error in {model_name} prediction for {task_name}: {e}")
                        task_predictions[model_name] = 0
                
                predictions[task_name] = task_predictions
                probabilities[task_name] = task_probabilities
            
            # Calculate ensemble predictions
            ensemble_predictions = {}
            ensemble_probabilities = {}
            
            for task_name in ['category', 'severity', 'priority']:
                task_preds = list(predictions[task_name].values())
                ensemble_pred = max(set(task_preds), key=task_preds.count)  # Majority vote
                ensemble_predictions[task_name] = ensemble_pred
                
                # Calculate ensemble probabilities
                if probabilities[task_name]:
                    task_probs = list(probabilities[task_name].values())
                    if task_probs:
                        ensemble_prob = np.mean(task_probs, axis=0)
                        ensemble_probabilities[task_name] = ensemble_prob.tolist()
            
            # Convert predictions to labels
            category_label = self._get_category_label(ensemble_predictions['category'])
            severity_label = self._get_severity_label(ensemble_predictions['severity'])
            priority_label = self._get_priority_label(ensemble_predictions['priority'])
            
            # Calculate confidence
            confidence = self._calculate_classification_confidence(ensemble_probabilities)
            
            # Generate recommendations
            recommendations = self._generate_classification_recommendations(
                category_label, severity_label, priority_label, confidence
            )
            
            return {
                'category': category_label,
                'severity': severity_label,
                'priority': priority_label,
                'confidence': confidence,
                'predictions': predictions,
                'probabilities': ensemble_probabilities,
                'recommendations': recommendations,
                'classification_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Incident classification failed: {e}")
            return self._get_fallback_classification(incident_data)
    
    async def classify_batch(self, incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify multiple incidents in batch."""
        try:
            results = []
            
            for incident in incidents:
                classification = await self.classify_incident(incident)
                results.append({
                    'incident_id': incident.get('id', 'unknown'),
                    'classification': classification
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Batch classification failed: {e}")
            return []
    
    def _prepare_training_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Prepare training data for classification models."""
        try:
            features = []
            categories = []
            severities = []
            priorities = []
            
            for _, row in data.iterrows():
                # Prepare feature vector
                feature_vector = self._extract_features(row.to_dict())
                features.append(feature_vector)
                
                # Extract targets
                category = row.get('category', 'unknown')
                severity = row.get('severity', 'MEDIUM')
                priority = row.get('priority', 'MEDIUM')
                
                categories.append(category)
                severities.append(severity)
                priorities.append(priority)
            
            # Encode labels
            categories_encoded = self.encoders['category'].fit_transform(categories)
            severities_encoded = self.encoders['severity'].fit_transform(severities)
            priorities_encoded = self.encoders['priority'].fit_transform(priorities)
            
            # Store class labels
            self.class_labels = self.encoders['category'].classes_.tolist()
            
            return (
                np.array(features),
                categories_encoded,
                severities_encoded,
                priorities_encoded
            )
            
        except Exception as e:
            logger.error(f"Training data preparation failed: {e}")
            return np.array([]), np.array([]), np.array([]), np.array([])
    
    def _prepare_features(self, incident_data: Dict[str, Any]) -> np.ndarray:
        """Prepare features for incident classification."""
        try:
            features = []
            
            # Text features
            message = incident_data.get('message', '')
            event_type = incident_data.get('event_type', '')
            source = incident_data.get('source', '')
            
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
                    message.count('warning')
                ])
            
            # Numeric features
            features.extend([
                incident_data.get('severity_score', 50) / 100.0,
                incident_data.get('confidence_score', 50) / 100.0,
                incident_data.get('anomaly_score', 0.5),
                incident_data.get('risk_score', 50) / 100.0,
                incident_data.get('threat_count', 1) / 10.0,
                incident_data.get('user_count', 1) / 100.0,
                incident_data.get('ip_count', 1) / 100.0,
                incident_data.get('port_count', 1) / 100.0
            ])
            
            # Categorical features (encoded)
            features.extend([
                1 if incident_data.get('is_internal', False) else 0,
                1 if incident_data.get('is_privileged', False) else 0,
                1 if incident_data.get('is_encrypted', False) else 0,
                1 if incident_data.get('has_malware', False) else 0,
                1 if incident_data.get('has_exploit', False) else 0,
                1 if incident_data.get('has_data_access', False) else 0
            ])
            
            # Time-based features
            timestamp = incident_data.get('timestamp', datetime.now().isoformat())
            try:
                dt = pd.to_datetime(timestamp)
                features.extend([
                    dt.hour / 24.0,
                    dt.dayofweek / 7.0,
                    dt.month / 12.0,
                    1 if dt.hour < 6 or dt.hour > 22 else 0  # Off-hours
                ])
            except:
                features.extend([0.5, 0.5, 0.5, 0])
            
            # Network features
            ip = incident_data.get('ip', '')
            features.extend([
                1 if ip.startswith(('10.', '192.168.', '172.')) else 0,  # Internal IP
                1 if ip.startswith(('127.', 'localhost')) else 0,  # Localhost
                len(ip.split('.')) if '.' in ip else 0  # IP format
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Feature preparation failed: {e}")
            return np.zeros(50)  # Return default feature vector
    
    def _extract_features(self, incident_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from incident data for training."""
        return self._prepare_features(incident_data)
    
    def _get_category_label(self, category_id: int) -> str:
        """Get category label from encoded ID."""
        try:
            if hasattr(self.encoders['category'], 'classes_'):
                return self.encoders['category'].classes_[category_id]
            else:
                return 'unknown'
        except:
            return 'unknown'
    
    def _get_severity_label(self, severity_id: int) -> str:
        """Get severity label from encoded ID."""
        try:
            if hasattr(self.encoders['severity'], 'classes_'):
                return self.encoders['severity'].classes_[severity_id]
            else:
                return 'MEDIUM'
        except:
            return 'MEDIUM'
    
    def _get_priority_label(self, priority_id: int) -> str:
        """Get priority label from encoded ID."""
        try:
            if hasattr(self.encoders['priority'], 'classes_'):
                return self.encoders['priority'].classes_[priority_id]
            else:
                return 'MEDIUM'
        except:
            return 'MEDIUM'
    
    def _calculate_classification_confidence(self, probabilities: Dict[str, List[float]]) -> float:
        """Calculate confidence in classification."""
        try:
            confidences = []
            
            for task_name, probs in probabilities.items():
                if probs:
                    # Confidence is the maximum probability
                    max_prob = max(probs)
                    confidences.append(max_prob)
            
            if confidences:
                return float(np.mean(confidences))
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5
    
    def _generate_classification_recommendations(
        self, 
        category: str, 
        severity: str, 
        priority: str, 
        confidence: float
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on classification."""
        recommendations = []
        
        # Category-specific recommendations
        if category in self.incident_categories:
            cat_info = self.incident_categories[category]
            recommendations.append({
                'type': 'category',
                'action': f'Follow {category} response procedures',
                'description': cat_info['description']
            })
        
        # Severity-based recommendations
        if severity == 'CRITICAL':
            recommendations.extend([
                {
                    'type': 'severity',
                    'action': 'Immediate response required',
                    'description': 'Critical severity incidents require immediate attention'
                },
                {
                    'type': 'severity',
                    'action': 'Notify executive team',
                    'description': 'Notify senior management of critical incident'
                }
            ])
        elif severity == 'HIGH':
            recommendations.append({
                'type': 'severity',
                'action': 'High priority response',
                'description': 'High severity incidents should be addressed within 1 hour'
            })
        
        # Priority-based recommendations
        if priority == 'URGENT':
            recommendations.append({
                'type': 'priority',
                'action': 'Escalate immediately',
                'description': 'Urgent priority incidents need immediate escalation'
            })
        
        # Confidence-based recommendations
        if confidence < 0.7:
            recommendations.append({
                'type': 'confidence',
                'action': 'Manual review recommended',
                'description': 'Low confidence classification - manual review recommended'
            })
        
        return recommendations
    
    def _calculate_model_performance(self, X: np.ndarray, y_category: np.ndarray, y_severity: np.ndarray, y_priority: np.ndarray):
        """Calculate model performance metrics."""
        try:
            self.model_performance = {
                'training_samples': len(X),
                'feature_count': X.shape[1],
                'category_classes': len(np.unique(y_category)),
                'severity_classes': len(np.unique(y_severity)),
                'priority_classes': len(np.unique(y_priority)),
                'last_training': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance calculation failed: {e}")
            self.model_performance = {}
    
    def _get_fallback_classification(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback classification when models are not trained."""
        # Simple rule-based classification
        message = incident_data.get('message', '').lower()
        severity = incident_data.get('severity', 'MEDIUM').upper()
        
        # Determine category based on keywords
        category = 'unknown'
        for cat_name, cat_info in self.incident_categories.items():
            if any(keyword in message for keyword in cat_info['keywords']):
                category = cat_name
                break
        
        # Determine priority based on severity
        priority = 'MEDIUM'
        if severity == 'CRITICAL':
            priority = 'URGENT'
        elif severity == 'HIGH':
            priority = 'HIGH'
        elif severity == 'LOW':
            priority = 'LOW'
        
        return {
            'category': category,
            'severity': severity,
            'priority': priority,
            'confidence': 0.3,
            'predictions': {},
            'probabilities': {},
            'recommendations': [{'type': 'general', 'action': 'Manual review required', 'description': 'Models not trained - manual review needed'}],
            'classification_timestamp': datetime.now().isoformat()
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
                model_path = os.path.join(save_path, f"{model_name}_classifier.joblib")
                joblib.dump(model, model_path)
            
            # Save scalers and encoders
            scaler_path = os.path.join(save_path, "classifier_scalers.joblib")
            joblib.dump(self.scalers, scaler_path)
            
            encoder_path = os.path.join(save_path, "classifier_encoders.joblib")
            joblib.dump(self.encoders, encoder_path)
            
            # Save vectorizers
            vectorizer_path = os.path.join(save_path, "classifier_vectorizers.joblib")
            joblib.dump(self.vectorizers, vectorizer_path)
            
            # Save feature importance
            importance_path = os.path.join(save_path, "classifier_feature_importance.json")
            with open(importance_path, 'w') as f:
                json.dump(self.feature_importance, f)
            
            logger.info(f"Incident classification models saved to {save_path}")
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
                model_path = os.path.join(load_path, f"{model_name}_classifier.joblib")
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
            
            # Load scalers and encoders
            scaler_path = os.path.join(load_path, "classifier_scalers.joblib")
            if os.path.exists(scaler_path):
                self.scalers = joblib.load(scaler_path)
            
            encoder_path = os.path.join(load_path, "classifier_encoders.joblib")
            if os.path.exists(encoder_path):
                self.encoders = joblib.load(encoder_path)
            
            # Load vectorizers
            vectorizer_path = os.path.join(load_path, "classifier_vectorizers.joblib")
            if os.path.exists(vectorizer_path):
                self.vectorizers = joblib.load(vectorizer_path)
            
            # Load feature importance
            importance_path = os.path.join(load_path, "classifier_feature_importance.json")
            if os.path.exists(importance_path):
                with open(importance_path, 'r') as f:
                    self.feature_importance = json.load(f)
            
            self.is_trained = True
            logger.info(f"Incident classification models loaded from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
