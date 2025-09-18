"""Dynamic risk scoring models for real-time risk assessment."""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import joblib
import os
import json

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb
import lightgbm as lgb

from ..config import SETTINGS

logger = logging.getLogger(__name__)


class RiskScorer:
    """Dynamic risk scoring models for real-time risk assessment."""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.model_performance = {}
        self.risk_factors = {}
        self.is_trained = False
        
        # Initialize models based on configuration
        self._initialize_models()
        self._load_risk_factors()
    
    def _initialize_models(self):
        """Initialize risk scoring models based on configuration."""
        model_type = SETTINGS.risk_model_type
        
        if model_type == "ensemble":
            self.models = {
                'random_forest': RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                ),
                'gradient_boosting': GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                ),
                'xgboost': xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    n_jobs=-1
                ),
                'lightgbm': lgb.LGBMRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    n_jobs=-1,
                    verbose=-1
                )
            }
            
            # Create ensemble model
            self.models['ensemble'] = VotingRegressor([
                ('rf', self.models['random_forest']),
                ('gb', self.models['gradient_boosting']),
                ('xgb', self.models['xgboost']),
                ('lgb', self.models['lightgbm'])
            ])
            
        elif model_type == "gradient_boosting":
            self.models = {
                'gradient_boosting': GradientBoostingRegressor(
                    n_estimators=200,
                    max_depth=8,
                    learning_rate=0.05,
                    random_state=42
                )
            }
            
        elif model_type == "neural_network":
            self.models = {
                'neural_network': MLPRegressor(
                    hidden_layer_sizes=(100, 50, 25),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    learning_rate='adaptive',
                    max_iter=1000,
                    random_state=42
                )
            }
        
        # Initialize scalers
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler()
        }
    
    def _load_risk_factors(self):
        """Load risk factors and their weights."""
        self.risk_factors = {
            'threat_severity': {
                'weights': {'LOW': 1, 'MEDIUM': 3, 'HIGH': 7, 'CRITICAL': 10},
                'description': 'Severity of the threat'
            },
            'asset_criticality': {
                'weights': {'LOW': 1, 'MEDIUM': 2, 'HIGH': 5, 'CRITICAL': 10},
                'description': 'Criticality of affected assets'
            },
            'vulnerability_exploitability': {
                'weights': {'LOW': 1, 'MEDIUM': 3, 'HIGH': 7, 'CRITICAL': 10},
                'description': 'Ease of exploiting the vulnerability'
            },
            'business_impact': {
                'weights': {'LOW': 1, 'MEDIUM': 3, 'HIGH': 7, 'CRITICAL': 10},
                'description': 'Potential business impact'
            },
            'detection_difficulty': {
                'weights': {'LOW': 10, 'MEDIUM': 7, 'HIGH': 3, 'CRITICAL': 1},
                'description': 'Difficulty of detecting the threat'
            },
            'threat_intelligence': {
                'weights': {'NONE': 1, 'LOW': 3, 'MEDIUM': 5, 'HIGH': 8, 'CRITICAL': 10},
                'description': 'Threat intelligence confidence'
            },
            'attack_sophistication': {
                'weights': {'LOW': 1, 'MEDIUM': 3, 'HIGH': 7, 'CRITICAL': 10},
                'description': 'Sophistication of the attack'
            },
            'data_sensitivity': {
                'weights': {'PUBLIC': 1, 'INTERNAL': 3, 'CONFIDENTIAL': 7, 'RESTRICTED': 10},
                'description': 'Sensitivity of affected data'
            }
        }
    
    async def train_models(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train risk scoring models."""
        try:
            logger.info("Starting risk scoring model training...")
            
            # Prepare features and target
            X, y = self._prepare_training_data(training_data)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
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
                    if model_name == 'ensemble':
                        # Ensemble needs unscaled data for some models
                        model.fit(X_train, y_train)
                        y_pred = model.predict(X_test)
                    else:
                        model.fit(X_train_scaled, y_train)
                        y_pred = model.predict(X_test_scaled)
                    
                    # Calculate metrics
                    mse = mean_squared_error(y_test, y_pred)
                    rmse = np.sqrt(mse)
                    mae = mean_absolute_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    
                    # Cross-validation score
                    if model_name == 'ensemble':
                        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
                    else:
                        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
                    
                    training_results[model_name] = {
                        'status': 'success',
                        'mse': float(mse),
                        'rmse': float(rmse),
                        'mae': float(mae),
                        'r2': float(r2),
                        'cv_mean': float(cv_scores.mean()),
                        'cv_std': float(cv_scores.std())
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
            logger.info("Risk scoring model training completed")
            
            return {
                'status': 'success',
                'models_trained': len([r for r in training_results.values() if r['status'] == 'success']),
                'training_results': training_results,
                'feature_importance': self.feature_importance,
                'model_performance': self.model_performance
            }
            
        except Exception as e:
            logger.error(f"Risk scoring training failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def calculate_risk_score(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate dynamic risk score for threat data."""
        try:
            if not self.is_trained:
                return self._get_fallback_risk_score(threat_data)
            
            # Prepare features
            features = self._prepare_features(threat_data)
            features_scaled = self.scalers['standard'].transform([features])
            
            # Get predictions from all models
            risk_scores = {}
            for model_name, model in self.models.items():
                try:
                    if model_name == 'ensemble':
                        score = model.predict([features])[0]
                    else:
                        score = model.predict(features_scaled)[0]
                    
                    # Ensure score is in valid range
                    score = max(0, min(100, score))
                    risk_scores[model_name] = float(score)
                    
                except Exception as e:
                    logger.error(f"Error in {model_name} prediction: {e}")
                    risk_scores[model_name] = 50.0
            
            # Calculate ensemble score
            ensemble_score = np.mean(list(risk_scores.values()))
            
            # Calculate confidence
            confidence = self._calculate_risk_confidence(risk_scores)
            
            # Determine risk level
            risk_level = self._determine_risk_level(ensemble_score)
            
            # Calculate risk factors
            risk_factors = self._calculate_risk_factors(threat_data)
            
            # Generate recommendations
            recommendations = self._generate_risk_recommendations(ensemble_score, risk_level, risk_factors)
            
            return {
                'risk_score': float(ensemble_score),
                'risk_level': risk_level,
                'confidence': confidence,
                'model_scores': risk_scores,
                'risk_factors': risk_factors,
                'feature_contributions': self._get_feature_contributions(threat_data, features),
                'recommendations': recommendations,
                'calculation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Risk score calculation failed: {e}")
            return self._get_fallback_risk_score(threat_data)
    
    async def calculate_portfolio_risk(self, threats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate portfolio-level risk from multiple threats."""
        try:
            if not threats:
                return {'portfolio_risk_score': 0, 'risk_level': 'LOW'}
            
            # Calculate individual risk scores
            individual_scores = []
            for threat in threats:
                risk_result = await self.calculate_risk_score(threat)
                individual_scores.append(risk_result['risk_score'])
            
            # Calculate portfolio metrics
            portfolio_score = np.mean(individual_scores)
            portfolio_std = np.std(individual_scores)
            max_risk = np.max(individual_scores)
            
            # Calculate risk distribution
            risk_levels = [self._determine_risk_level(score) for score in individual_scores]
            risk_distribution = {}
            for level in risk_levels:
                risk_distribution[level] = risk_distribution.get(level, 0) + 1
            
            # Determine portfolio risk level
            portfolio_risk_level = self._determine_risk_level(portfolio_score)
            
            # Calculate correlation risk
            correlation_risk = self._calculate_correlation_risk(threats)
            
            # Generate portfolio recommendations
            recommendations = self._generate_portfolio_recommendations(
                portfolio_score, portfolio_std, max_risk, risk_distribution
            )
            
            return {
                'portfolio_risk_score': float(portfolio_score),
                'portfolio_risk_level': portfolio_risk_level,
                'risk_std': float(portfolio_std),
                'max_individual_risk': float(max_risk),
                'risk_distribution': risk_distribution,
                'correlation_risk': correlation_risk,
                'individual_scores': individual_scores,
                'recommendations': recommendations,
                'calculation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Portfolio risk calculation failed: {e}")
            return {'portfolio_risk_score': 50, 'risk_level': 'MEDIUM', 'error': str(e)}
    
    def _prepare_training_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for risk scoring models."""
        try:
            # Extract features
            features = []
            targets = []
            
            for _, row in data.iterrows():
                # Prepare feature vector
                feature_vector = self._extract_features(row.to_dict())
                features.append(feature_vector)
                
                # Extract target (risk score)
                target = row.get('risk_score', 50)  # Default to medium risk
                targets.append(target)
            
            return np.array(features), np.array(targets)
            
        except Exception as e:
            logger.error(f"Training data preparation failed: {e}")
            return np.array([]), np.array([])
    
    def _prepare_features(self, threat_data: Dict[str, Any]) -> np.ndarray:
        """Prepare features for risk scoring."""
        try:
            features = []
            
            # Threat severity
            severity = threat_data.get('severity', 'MEDIUM').upper()
            severity_score = self.risk_factors['threat_severity']['weights'].get(severity, 5)
            features.append(severity_score)
            
            # Asset criticality
            asset_criticality = threat_data.get('asset_criticality', 'MEDIUM').upper()
            asset_score = self.risk_factors['asset_criticality']['weights'].get(asset_criticality, 5)
            features.append(asset_score)
            
            # Vulnerability exploitability
            exploitability = threat_data.get('vulnerability_exploitability', 'MEDIUM').upper()
            exploit_score = self.risk_factors['vulnerability_exploitability']['weights'].get(exploitability, 5)
            features.append(exploit_score)
            
            # Business impact
            business_impact = threat_data.get('business_impact', 'MEDIUM').upper()
            business_score = self.risk_factors['business_impact']['weights'].get(business_impact, 5)
            features.append(business_score)
            
            # Detection difficulty
            detection_difficulty = threat_data.get('detection_difficulty', 'MEDIUM').upper()
            detection_score = self.risk_factors['detection_difficulty']['weights'].get(detection_difficulty, 5)
            features.append(detection_score)
            
            # Threat intelligence
            threat_intel = threat_data.get('threat_intelligence', 'MEDIUM').upper()
            intel_score = self.risk_factors['threat_intelligence']['weights'].get(threat_intel, 5)
            features.append(intel_score)
            
            # Attack sophistication
            sophistication = threat_data.get('attack_sophistication', 'MEDIUM').upper()
            soph_score = self.risk_factors['attack_sophistication']['weights'].get(sophistication, 5)
            features.append(soph_score)
            
            # Data sensitivity
            data_sensitivity = threat_data.get('data_sensitivity', 'INTERNAL').upper()
            data_score = self.risk_factors['data_sensitivity']['weights'].get(data_sensitivity, 5)
            features.append(data_score)
            
            # Additional features
            features.extend([
                threat_data.get('confidence_score', 50) / 100.0,  # Normalize to 0-1
                threat_data.get('anomaly_score', 0.5),  # Already normalized
                threat_data.get('threat_count', 1) / 10.0,  # Normalize threat count
                threat_data.get('time_since_last_incident', 24) / 24.0,  # Hours to days
                threat_data.get('user_privilege_level', 3) / 5.0,  # Normalize privilege level
                threat_data.get('network_segment_risk', 0.5),  # Already normalized
                threat_data.get('geographic_risk', 0.5),  # Already normalized
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Feature preparation failed: {e}")
            return np.zeros(15)  # Return default feature vector
    
    def _extract_features(self, threat_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from threat data for training."""
        return self._prepare_features(threat_data)
    
    def _calculate_risk_factors(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate individual risk factors."""
        factors = {}
        
        for factor_name, factor_config in self.risk_factors.items():
            value = threat_data.get(factor_name, 'MEDIUM').upper()
            weight = factor_config['weights'].get(value, 5)
            factors[factor_name] = {
                'value': value,
                'weight': weight,
                'description': factor_config['description']
            }
        
        return factors
    
    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level from score."""
        if score >= 80:
            return 'CRITICAL'
        elif score >= 60:
            return 'HIGH'
        elif score >= 40:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_risk_confidence(self, scores: Dict[str, float]) -> float:
        """Calculate confidence in risk score."""
        try:
            score_values = list(scores.values())
            if len(score_values) < 2:
                return 0.5
            
            # Calculate consistency (inverse of standard deviation)
            std_dev = np.std(score_values)
            mean_score = np.mean(score_values)
            
            # Higher confidence for lower standard deviation
            consistency = 1.0 / (1.0 + std_dev)
            
            # Higher confidence for scores closer to 0 or 100 (clear decisions)
            clarity = 1.0 - abs(mean_score - 50) / 50.0
            
            # Combine factors
            confidence = (consistency * 0.7) + (clarity * 0.3)
            
            return float(max(0.0, min(1.0, confidence)))
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5
    
    def _calculate_correlation_risk(self, threats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate correlation risk between threats."""
        try:
            if len(threats) < 2:
                return {'correlation_score': 0.0, 'correlation_level': 'LOW'}
            
            # Extract common features for correlation analysis
            features = []
            for threat in threats:
                feature_vector = self._prepare_features(threat)
                features.append(feature_vector)
            
            features_array = np.array(features)
            
            # Calculate correlation matrix
            correlation_matrix = np.corrcoef(features_array)
            
            # Calculate average correlation (excluding diagonal)
            mask = ~np.eye(correlation_matrix.shape[0], dtype=bool)
            avg_correlation = np.mean(correlation_matrix[mask])
            
            # Determine correlation level
            if avg_correlation > 0.7:
                correlation_level = 'HIGH'
            elif avg_correlation > 0.4:
                correlation_level = 'MEDIUM'
            else:
                correlation_level = 'LOW'
            
            return {
                'correlation_score': float(avg_correlation),
                'correlation_level': correlation_level,
                'max_correlation': float(np.max(correlation_matrix[mask])),
                'min_correlation': float(np.min(correlation_matrix[mask]))
            }
            
        except Exception as e:
            logger.error(f"Correlation risk calculation failed: {e}")
            return {'correlation_score': 0.0, 'correlation_level': 'LOW'}
    
    def _get_feature_contributions(self, threat_data: Dict[str, Any], features: np.ndarray) -> Dict[str, float]:
        """Get feature contributions to risk score."""
        try:
            # Use feature importance from the best model
            if 'ensemble' in self.feature_importance:
                importances = self.feature_importance['ensemble']
            elif self.feature_importance:
                importances = list(self.feature_importance.values())[0]
            else:
                return {}
            
            feature_names = [
                'threat_severity', 'asset_criticality', 'vulnerability_exploitability',
                'business_impact', 'detection_difficulty', 'threat_intelligence',
                'attack_sophistication', 'data_sensitivity', 'confidence_score',
                'anomaly_score', 'threat_count', 'time_since_last_incident',
                'user_privilege_level', 'network_segment_risk', 'geographic_risk'
            ]
            
            # Ensure we have the right number of features
            if len(importances) >= len(feature_names):
                contributions = dict(zip(feature_names, importances[:len(feature_names)]))
            else:
                contributions = dict(zip(feature_names[:len(importances)], importances))
            
            return contributions
            
        except Exception as e:
            logger.error(f"Feature contribution calculation failed: {e}")
            return {}
    
    def _generate_risk_recommendations(self, score: float, risk_level: str, risk_factors: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate risk-based recommendations."""
        recommendations = []
        
        # High-level recommendations based on risk level
        if risk_level == 'CRITICAL':
            recommendations.extend([
                {
                    'priority': 'IMMEDIATE',
                    'action': 'Isolate affected systems',
                    'description': 'Immediately isolate systems to prevent further compromise'
                },
                {
                    'priority': 'IMMEDIATE',
                    'action': 'Activate incident response team',
                    'description': 'Engage full incident response team'
                },
                {
                    'priority': 'HIGH',
                    'action': 'Notify stakeholders',
                    'description': 'Notify executive team and relevant stakeholders'
                }
            ])
        elif risk_level == 'HIGH':
            recommendations.extend([
                {
                    'priority': 'HIGH',
                    'action': 'Implement additional monitoring',
                    'description': 'Increase monitoring and alerting for affected systems'
                },
                {
                    'priority': 'HIGH',
                    'action': 'Review access controls',
                    'description': 'Review and tighten access controls'
                },
                {
                    'priority': 'MEDIUM',
                    'action': 'Update security policies',
                    'description': 'Review and update security policies as needed'
                }
            ])
        elif risk_level == 'MEDIUM':
            recommendations.extend([
                {
                    'priority': 'MEDIUM',
                    'action': 'Monitor closely',
                    'description': 'Monitor the situation closely for escalation'
                },
                {
                    'priority': 'MEDIUM',
                    'action': 'Document findings',
                    'description': 'Document findings and lessons learned'
                }
            ])
        else:
            recommendations.append({
                'priority': 'LOW',
                'action': 'Continue monitoring',
                'description': 'Continue normal monitoring procedures'
            })
        
        # Factor-specific recommendations
        for factor_name, factor_data in risk_factors.items():
            if factor_data['weight'] >= 7:  # High weight factors
                if factor_name == 'threat_severity':
                    recommendations.append({
                        'priority': 'HIGH',
                        'action': 'Address high severity threat',
                        'description': 'Focus on mitigating the high severity threat'
                    })
                elif factor_name == 'business_impact':
                    recommendations.append({
                        'priority': 'HIGH',
                        'action': 'Minimize business impact',
                        'description': 'Implement measures to reduce business impact'
                    })
                elif factor_name == 'data_sensitivity':
                    recommendations.append({
                        'priority': 'HIGH',
                        'action': 'Protect sensitive data',
                        'description': 'Implement additional data protection measures'
                    })
        
        return recommendations
    
    def _generate_portfolio_recommendations(
        self, 
        portfolio_score: float, 
        portfolio_std: float, 
        max_risk: float, 
        risk_distribution: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """Generate portfolio-level recommendations."""
        recommendations = []
        
        # High-level portfolio recommendations
        if portfolio_score >= 70:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Portfolio-wide security review',
                'description': 'Conduct comprehensive security review of all systems'
            })
        
        # High variance recommendations
        if portfolio_std > 20:
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Standardize risk assessment',
                'description': 'Implement standardized risk assessment processes'
            })
        
        # High individual risk recommendations
        if max_risk >= 80:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Address highest risk threats',
                'description': 'Focus on mitigating the highest risk individual threats'
            })
        
        # Risk distribution recommendations
        critical_count = risk_distribution.get('CRITICAL', 0)
        high_count = risk_distribution.get('HIGH', 0)
        
        if critical_count > 0:
            recommendations.append({
                'priority': 'IMMEDIATE',
                'action': 'Address critical risks',
                'description': f'Immediately address {critical_count} critical risk(s)'
            })
        
        if high_count > 5:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Increase security resources',
                'description': f'Consider increasing security team resources for {high_count} high-risk threats'
            })
        
        return recommendations
    
    def _calculate_model_performance(self, X: np.ndarray, y: np.ndarray):
        """Calculate model performance metrics."""
        try:
            self.model_performance = {
                'training_samples': len(X),
                'feature_count': X.shape[1],
                'target_mean': float(np.mean(y)),
                'target_std': float(np.std(y)),
                'last_training': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance calculation failed: {e}")
            self.model_performance = {}
    
    def _get_fallback_risk_score(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback risk score when models are not trained."""
        # Simple rule-based scoring
        severity = threat_data.get('severity', 'MEDIUM').upper()
        severity_scores = {'LOW': 20, 'MEDIUM': 50, 'HIGH': 80, 'CRITICAL': 95}
        base_score = severity_scores.get(severity, 50)
        
        return {
            'risk_score': float(base_score),
            'risk_level': self._determine_risk_level(base_score),
            'confidence': 0.3,
            'model_scores': {},
            'risk_factors': {},
            'feature_contributions': {},
            'recommendations': [{'priority': 'LOW', 'action': 'Manual review required', 'description': 'Models not trained - manual review needed'}],
            'calculation_timestamp': datetime.now().isoformat()
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
                model_path = os.path.join(save_path, f"{model_name}_risk_model.joblib")
                joblib.dump(model, model_path)
            
            # Save scalers
            scaler_path = os.path.join(save_path, "risk_scalers.joblib")
            joblib.dump(self.scalers, scaler_path)
            
            # Save feature importance
            importance_path = os.path.join(save_path, "risk_feature_importance.json")
            with open(importance_path, 'w') as f:
                json.dump(self.feature_importance, f)
            
            logger.info(f"Risk scoring models saved to {save_path}")
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
                model_path = os.path.join(load_path, f"{model_name}_risk_model.joblib")
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
            
            # Load scalers
            scaler_path = os.path.join(load_path, "risk_scalers.joblib")
            if os.path.exists(scaler_path):
                self.scalers = joblib.load(scaler_path)
            
            # Load feature importance
            importance_path = os.path.join(load_path, "risk_feature_importance.json")
            if os.path.exists(importance_path):
                with open(importance_path, 'r') as f:
                    self.feature_importance = json.load(f)
            
            self.is_trained = True
            logger.info(f"Risk scoring models loaded from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
