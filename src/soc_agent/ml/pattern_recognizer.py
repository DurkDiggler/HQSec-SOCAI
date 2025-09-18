"""Attack pattern recognition and campaign detection models."""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import joblib
import os
import json

from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import hdbscan
import umap

from ..config import SETTINGS

logger = logging.getLogger(__name__)


class PatternRecognizer:
    """Attack pattern recognition and campaign detection system."""
    
    def __init__(self):
        self.clustering_models = {}
        self.scalers = {}
        self.encoders = {}
        self.pattern_database = {}
        self.campaign_patterns = {}
        self.model_performance = {}
        self.is_trained = False
        
        # Attack patterns
        self.attack_patterns = {
            'reconnaissance': {
                'keywords': ['scan', 'probe', 'enumerate', 'discover', 'recon'],
                'indicators': ['port_scan', 'service_scan', 'os_detection', 'vulnerability_scan']
            },
            'initial_access': {
                'keywords': ['login', 'auth', 'access', 'breach', 'exploit'],
                'indicators': ['brute_force', 'credential_stuffing', 'phishing', 'exploit']
            },
            'execution': {
                'keywords': ['execute', 'run', 'launch', 'start', 'command'],
                'indicators': ['command_execution', 'script_execution', 'process_creation']
            },
            'persistence': {
                'keywords': ['persist', 'maintain', 'survive', 'survive', 'backdoor'],
                'indicators': ['registry_modification', 'scheduled_task', 'service_creation']
            },
            'privilege_escalation': {
                'keywords': ['escalate', 'privilege', 'admin', 'root', 'elevate'],
                'indicators': ['privilege_escalation', 'token_manipulation', 'exploit']
            },
            'defense_evasion': {
                'keywords': ['evade', 'bypass', 'hide', 'obfuscate', 'disguise'],
                'indicators': ['process_hollowing', 'dll_injection', 'packing']
            },
            'credential_access': {
                'keywords': ['credential', 'password', 'hash', 'token', 'key'],
                'indicators': ['credential_dumping', 'keylogging', 'password_spraying']
            },
            'discovery': {
                'keywords': ['discover', 'enumerate', 'explore', 'map', 'find'],
                'indicators': ['network_discovery', 'system_discovery', 'process_discovery']
            },
            'lateral_movement': {
                'keywords': ['lateral', 'move', 'pivot', 'spread', 'propagate'],
                'indicators': ['remote_execution', 'pass_the_hash', 'wmi_execution']
            },
            'collection': {
                'keywords': ['collect', 'gather', 'harvest', 'extract', 'steal'],
                'indicators': ['data_collection', 'screen_capture', 'keylogging']
            },
            'command_control': {
                'keywords': ['c2', 'command', 'control', 'beacon', 'callback'],
                'indicators': ['c2_communication', 'dns_tunneling', 'http_tunneling']
            },
            'exfiltration': {
                'keywords': ['exfiltrate', 'steal', 'extract', 'transfer', 'upload'],
                'indicators': ['data_exfiltration', 'ftp_upload', 'cloud_upload']
            },
            'impact': {
                'keywords': ['impact', 'damage', 'destroy', 'corrupt', 'encrypt'],
                'indicators': ['data_destruction', 'service_disruption', 'ransomware']
            }
        }
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize pattern recognition models."""
        self.clustering_models = {
            'dbscan': DBSCAN(eps=0.5, min_samples=5),
            'kmeans': KMeans(n_clusters=8, random_state=42),
            'hdbscan': hdbscan.HDBSCAN(min_cluster_size=5),
            'agglomerative': AgglomerativeClustering(n_clusters=8)
        }
        
        # Initialize scalers and encoders
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': StandardScaler()
        }
        
        self.encoders = {
            'label': LabelEncoder()
        }
    
    async def train_models(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train pattern recognition models."""
        try:
            logger.info("Starting pattern recognition model training...")
            
            # Prepare features
            X = self._prepare_features(training_data)
            
            # Scale features
            X_scaled = self.scalers['standard'].fit_transform(X)
            
            # Train clustering models
            training_results = {}
            for model_name, model in self.clustering_models.items():
                try:
                    logger.info(f"Training {model_name}...")
                    
                    # Fit model
                    labels = model.fit_predict(X_scaled)
                    
                    # Calculate clustering metrics
                    if len(set(labels)) > 1:
                        silhouette = silhouette_score(X_scaled, labels)
                        calinski = calinski_harabasz_score(X_scaled, labels)
                    else:
                        silhouette = -1
                        calinski = 0
                    
                    training_results[model_name] = {
                        'status': 'success',
                        'n_clusters': len(set(labels)) - (1 if -1 in labels else 0),
                        'n_noise': list(labels).count(-1) if -1 in labels else 0,
                        'silhouette_score': float(silhouette),
                        'calinski_harabasz_score': float(calinski)
                    }
                    
                except Exception as e:
                    logger.error(f"Error training {model_name}: {e}")
                    training_results[model_name] = {'status': 'failed', 'error': str(e)}
            
            # Build pattern database
            self._build_pattern_database(X_scaled, training_data)
            
            # Calculate overall performance
            self._calculate_model_performance(X)
            
            self.is_trained = True
            logger.info("Pattern recognition model training completed")
            
            return {
                'status': 'success',
                'training_results': training_results,
                'pattern_database_size': len(self.pattern_database),
                'model_performance': self.model_performance
            }
            
        except Exception as e:
            logger.error(f"Pattern recognition training failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def detect_attack_patterns(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect attack patterns in event data."""
        try:
            if not self.is_trained:
                return self._get_fallback_pattern_detection(event_data)
            
            # Prepare features
            features = self._prepare_features(pd.DataFrame([event_data]))
            features_scaled = self.scalers['standard'].transform(features)
            
            # Detect patterns
            patterns = self._analyze_patterns(event_data, features_scaled[0])
            
            # Detect campaigns
            campaigns = await self._detect_campaigns(event_data, features_scaled[0])
            
            # Calculate pattern confidence
            confidence = self._calculate_pattern_confidence(patterns, campaigns)
            
            # Generate recommendations
            recommendations = self._generate_pattern_recommendations(patterns, campaigns)
            
            return {
                'patterns_detected': patterns,
                'campaigns_detected': campaigns,
                'confidence': confidence,
                'pattern_count': len(patterns),
                'campaign_count': len(campaigns),
                'recommendations': recommendations,
                'detection_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Attack pattern detection failed: {e}")
            return self._get_fallback_pattern_detection(event_data)
    
    async def detect_campaigns(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect attack campaigns from multiple events."""
        try:
            if len(events) < 2:
                return {'campaigns': [], 'campaign_count': 0}
            
            # Convert to DataFrame
            events_df = pd.DataFrame(events)
            
            # Prepare features
            X = self._prepare_features(events_df)
            X_scaled = self.scalers['standard'].transform(X)
            
            # Cluster events
            cluster_labels = self.clustering_models['dbscan'].fit_predict(X_scaled)
            
            # Group events by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(events[i])
            
            # Analyze clusters for campaigns
            campaigns = []
            for cluster_id, cluster_events in clusters.items():
                if cluster_id == -1 or len(cluster_events) < 2:
                    continue
                
                campaign = self._analyze_campaign(cluster_events, cluster_id)
                if campaign:
                    campaigns.append(campaign)
            
            return {
                'campaigns': campaigns,
                'campaign_count': len(campaigns),
                'total_events': len(events),
                'clustered_events': len([e for e in cluster_labels if e != -1]),
                'detection_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Campaign detection failed: {e}")
            return {'campaigns': [], 'campaign_count': 0, 'error': str(e)}
    
    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features for pattern recognition."""
        try:
            features = []
            
            for _, row in data.iterrows():
                feature_vector = self._extract_features(row.to_dict())
                features.append(feature_vector)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Feature preparation failed: {e}")
            return np.zeros((len(data), 10))
    
    def _extract_features(self, event_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from event data."""
        try:
            features = []
            
            # Text features
            message = event_data.get('message', '').lower()
            event_type = event_data.get('event_type', '').lower()
            source = event_data.get('source', '').lower()
            
            # Pattern matching features
            pattern_scores = []
            for pattern_name, pattern_info in self.attack_patterns.items():
                score = 0.0
                for keyword in pattern_info['keywords']:
                    if keyword in message or keyword in event_type:
                        score += 1.0
                pattern_scores.append(score / len(pattern_info['keywords']))
            
            features.extend(pattern_scores)
            
            # Numeric features
            features.extend([
                event_data.get('severity_score', 50) / 100.0,
                event_data.get('confidence_score', 50) / 100.0,
                event_data.get('anomaly_score', 0.5),
                event_data.get('risk_score', 50) / 100.0
            ])
            
            # Time features
            timestamp = event_data.get('timestamp', datetime.now().isoformat())
            try:
                dt = pd.to_datetime(timestamp)
                features.extend([
                    dt.hour / 24.0,
                    dt.dayofweek / 7.0,
                    dt.month / 12.0
                ])
            except:
                features.extend([0.5, 0.5, 0.5])
            
            # Network features
            ip = event_data.get('ip', '')
            features.extend([
                1 if ip.startswith(('10.', '192.168.', '172.')) else 0,
                1 if ip.startswith(('127.', 'localhost')) else 0,
                len(ip.split('.')) if '.' in ip else 0
            ])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return np.zeros(20)
    
    def _analyze_patterns(self, event_data: Dict[str, Any], features: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze event for attack patterns."""
        patterns = []
        
        try:
            message = event_data.get('message', '').lower()
            event_type = event_data.get('event_type', '').lower()
            
            for pattern_name, pattern_info in self.attack_patterns.items():
                score = 0.0
                matched_keywords = []
                
                for keyword in pattern_info['keywords']:
                    if keyword in message or keyword in event_type:
                        score += 1.0
                        matched_keywords.append(keyword)
                
                if score > 0:
                    confidence = score / len(pattern_info['keywords'])
                    patterns.append({
                        'pattern_name': pattern_name,
                        'confidence': confidence,
                        'matched_keywords': matched_keywords,
                        'description': pattern_info.get('description', ''),
                        'indicators': pattern_info.get('indicators', [])
                    })
            
            # Sort by confidence
            patterns.sort(key=lambda x: x['confidence'], reverse=True)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return []
    
    async def _detect_campaigns(self, event_data: Dict[str, Any], features: np.ndarray) -> List[Dict[str, Any]]:
        """Detect campaigns involving this event."""
        campaigns = []
        
        try:
            # Check against known campaign patterns
            for campaign_id, campaign_info in self.campaign_patterns.items():
                similarity = self._calculate_campaign_similarity(event_data, campaign_info)
                
                if similarity > SETTINGS.pattern_similarity_threshold:
                    campaigns.append({
                        'campaign_id': campaign_id,
                        'similarity': similarity,
                        'campaign_info': campaign_info
                    })
            
            return campaigns
            
        except Exception as e:
            logger.error(f"Campaign detection failed: {e}")
            return []
    
    def _analyze_campaign(self, events: List[Dict[str, Any]], cluster_id: int) -> Optional[Dict[str, Any]]:
        """Analyze a cluster of events for campaign characteristics."""
        try:
            if len(events) < 2:
                return None
            
            # Extract common patterns
            common_patterns = self._extract_common_patterns(events)
            
            # Calculate campaign metrics
            campaign_metrics = self._calculate_campaign_metrics(events)
            
            # Determine campaign type
            campaign_type = self._determine_campaign_type(common_patterns, campaign_metrics)
            
            # Calculate confidence
            confidence = self._calculate_campaign_confidence(events, common_patterns)
            
            return {
                'campaign_id': f"campaign_{cluster_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'cluster_id': cluster_id,
                'event_count': len(events),
                'campaign_type': campaign_type,
                'common_patterns': common_patterns,
                'metrics': campaign_metrics,
                'confidence': confidence,
                'start_time': min(event.get('timestamp', '') for event in events),
                'end_time': max(event.get('timestamp', '') for event in events),
                'affected_ips': list(set(event.get('ip', '') for event in events)),
                'affected_users': list(set(event.get('user', '') for event in events))
            }
            
        except Exception as e:
            logger.error(f"Campaign analysis failed: {e}")
            return None
    
    def _extract_common_patterns(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract common patterns from a group of events."""
        patterns = []
        
        try:
            # Count pattern occurrences
            pattern_counts = {}
            for event in events:
                event_patterns = self._analyze_patterns(event, np.zeros(20))
                for pattern in event_patterns:
                    pattern_name = pattern['pattern_name']
                    if pattern_name not in pattern_counts:
                        pattern_counts[pattern_name] = 0
                    pattern_counts[pattern_name] += 1
            
            # Create common patterns
            for pattern_name, count in pattern_counts.items():
                if count >= len(events) * 0.5:  # Present in at least 50% of events
                    patterns.append({
                        'pattern_name': pattern_name,
                        'frequency': count / len(events),
                        'description': self.attack_patterns[pattern_name].get('description', '')
                    })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Common pattern extraction failed: {e}")
            return []
    
    def _calculate_campaign_metrics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate campaign metrics."""
        try:
            metrics = {
                'duration_hours': 0,
                'unique_ips': 0,
                'unique_users': 0,
                'unique_sources': 0,
                'severity_distribution': {},
                'event_types': set()
            }
            
            if not events:
                return metrics
            
            # Calculate duration
            timestamps = [event.get('timestamp', '') for event in events]
            if timestamps:
                start_time = min(pd.to_datetime(timestamps))
                end_time = max(pd.to_datetime(timestamps))
                metrics['duration_hours'] = (end_time - start_time).total_seconds() / 3600
            
            # Calculate unique counts
            metrics['unique_ips'] = len(set(event.get('ip', '') for event in events))
            metrics['unique_users'] = len(set(event.get('user', '') for event in events))
            metrics['unique_sources'] = len(set(event.get('source', '') for event in events))
            
            # Calculate severity distribution
            severities = [event.get('severity', 'MEDIUM') for event in events]
            for severity in severities:
                metrics['severity_distribution'][severity] = metrics['severity_distribution'].get(severity, 0) + 1
            
            # Calculate event types
            metrics['event_types'] = list(set(event.get('event_type', '') for event in events))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Campaign metrics calculation failed: {e}")
            return {}
    
    def _determine_campaign_type(self, patterns: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
        """Determine the type of campaign based on patterns and metrics."""
        try:
            if not patterns:
                return 'unknown'
            
            # Get most frequent pattern
            most_frequent = max(patterns, key=lambda x: x['frequency'])
            pattern_name = most_frequent['pattern_name']
            
            # Map pattern to campaign type
            campaign_type_mapping = {
                'reconnaissance': 'Reconnaissance Campaign',
                'initial_access': 'Initial Access Campaign',
                'execution': 'Execution Campaign',
                'persistence': 'Persistence Campaign',
                'privilege_escalation': 'Privilege Escalation Campaign',
                'defense_evasion': 'Defense Evasion Campaign',
                'credential_access': 'Credential Access Campaign',
                'discovery': 'Discovery Campaign',
                'lateral_movement': 'Lateral Movement Campaign',
                'collection': 'Data Collection Campaign',
                'command_control': 'C2 Campaign',
                'exfiltration': 'Data Exfiltration Campaign',
                'impact': 'Impact Campaign'
            }
            
            return campaign_type_mapping.get(pattern_name, 'Unknown Campaign')
            
        except Exception as e:
            logger.error(f"Campaign type determination failed: {e}")
            return 'unknown'
    
    def _calculate_campaign_confidence(self, events: List[Dict[str, Any]], patterns: List[Dict[str, Any]]) -> float:
        """Calculate confidence in campaign detection."""
        try:
            if not events or not patterns:
                return 0.0
            
            # Base confidence on pattern frequency
            pattern_confidence = sum(pattern['frequency'] for pattern in patterns) / len(patterns)
            
            # Adjust for event count
            event_confidence = min(1.0, len(events) / 10.0)
            
            # Adjust for diversity
            diversity_confidence = min(1.0, len(set(event.get('ip', '') for event in events)) / 5.0)
            
            # Combine confidences
            confidence = (pattern_confidence * 0.5) + (event_confidence * 0.3) + (diversity_confidence * 0.2)
            
            return float(confidence)
            
        except Exception as e:
            logger.error(f"Campaign confidence calculation failed: {e}")
            return 0.0
    
    def _calculate_campaign_similarity(self, event_data: Dict[str, Any], campaign_info: Dict[str, Any]) -> float:
        """Calculate similarity between event and campaign."""
        try:
            # Extract event features
            event_features = self._extract_features(event_data)
            
            # Extract campaign features (average of campaign events)
            campaign_features = campaign_info.get('average_features', np.zeros(20))
            
            # Calculate cosine similarity
            similarity = np.dot(event_features, campaign_features) / (
                np.linalg.norm(event_features) * np.linalg.norm(campaign_features)
            )
            
            return float(similarity) if not np.isnan(similarity) else 0.0
            
        except Exception as e:
            logger.error(f"Campaign similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_pattern_confidence(self, patterns: List[Dict[str, Any]], campaigns: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in pattern detection."""
        try:
            if not patterns and not campaigns:
                return 0.0
            
            pattern_confidence = np.mean([p['confidence'] for p in patterns]) if patterns else 0.0
            campaign_confidence = np.mean([c['similarity'] for c in campaigns]) if campaigns else 0.0
            
            # Weight pattern confidence more heavily
            overall_confidence = (pattern_confidence * 0.7) + (campaign_confidence * 0.3)
            
            return float(overall_confidence)
            
        except Exception as e:
            logger.error(f"Pattern confidence calculation failed: {e}")
            return 0.0
    
    def _generate_pattern_recommendations(self, patterns: List[Dict[str, Any]], campaigns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on detected patterns and campaigns."""
        recommendations = []
        
        try:
            # Pattern-based recommendations
            for pattern in patterns:
                if pattern['confidence'] > 0.7:
                    recommendations.append({
                        'type': 'pattern',
                        'action': f'Investigate {pattern["pattern_name"]} pattern',
                        'description': f'High confidence {pattern["pattern_name"]} pattern detected',
                        'priority': 'HIGH'
                    })
            
            # Campaign-based recommendations
            for campaign in campaigns:
                if campaign['similarity'] > 0.8:
                    recommendations.append({
                        'type': 'campaign',
                        'action': 'Investigate campaign activity',
                        'description': f'High similarity to known campaign: {campaign["campaign_id"]}',
                        'priority': 'HIGH'
                    })
            
            # General recommendations
            if len(patterns) > 3:
                recommendations.append({
                    'type': 'general',
                    'action': 'Comprehensive investigation required',
                    'description': 'Multiple attack patterns detected - comprehensive investigation needed',
                    'priority': 'HIGH'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return []
    
    def _build_pattern_database(self, X_scaled: np.ndarray, training_data: pd.DataFrame):
        """Build pattern database from training data."""
        try:
            # Cluster the data
            cluster_labels = self.clustering_models['dbscan'].fit_predict(X_scaled)
            
            # Group events by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(training_data.iloc[i].to_dict())
            
            # Build pattern database
            for cluster_id, cluster_events in clusters.items():
                if cluster_id == -1 or len(cluster_events) < 2:
                    continue
                
                # Calculate average features
                cluster_features = X_scaled[cluster_labels == cluster_id]
                average_features = np.mean(cluster_features, axis=0)
                
                # Store pattern
                self.pattern_database[f"pattern_{cluster_id}"] = {
                    'cluster_id': cluster_id,
                    'event_count': len(cluster_events),
                    'average_features': average_features.tolist(),
                    'events': cluster_events
                }
            
        except Exception as e:
            logger.error(f"Pattern database building failed: {e}")
    
    def _calculate_model_performance(self, X: np.ndarray):
        """Calculate model performance metrics."""
        try:
            self.model_performance = {
                'training_samples': len(X),
                'feature_count': X.shape[1],
                'pattern_database_size': len(self.pattern_database),
                'last_training': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance calculation failed: {e}")
            self.model_performance = {}
    
    def _get_fallback_pattern_detection(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback pattern detection when models are not trained."""
        # Simple rule-based pattern detection
        message = event_data.get('message', '').lower()
        event_type = event_data.get('event_type', '').lower()
        
        patterns = []
        for pattern_name, pattern_info in self.attack_patterns.items():
            if any(keyword in message or keyword in event_type for keyword in pattern_info['keywords']):
                patterns.append({
                    'pattern_name': pattern_name,
                    'confidence': 0.5,
                    'matched_keywords': [],
                    'description': pattern_info.get('description', ''),
                    'indicators': pattern_info.get('indicators', [])
                })
        
        return {
            'patterns_detected': patterns,
            'campaigns_detected': [],
            'confidence': 0.3,
            'pattern_count': len(patterns),
            'campaign_count': 0,
            'recommendations': [{'type': 'general', 'action': 'Manual review required', 'description': 'Models not trained - manual review needed'}],
            'detection_timestamp': datetime.now().isoformat()
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
            for model_name, model in self.clustering_models.items():
                model_path = os.path.join(save_path, f"{model_name}_pattern_model.joblib")
                joblib.dump(model, model_path)
            
            # Save scalers
            scaler_path = os.path.join(save_path, "pattern_scalers.joblib")
            joblib.dump(self.scalers, scaler_path)
            
            # Save pattern database
            pattern_path = os.path.join(save_path, "pattern_database.json")
            with open(pattern_path, 'w') as f:
                json.dump(self.pattern_database, f)
            
            logger.info(f"Pattern recognition models saved to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
            return False
    
    def load_models(self, path: str = None) -> bool:
        """Load trained models from disk."""
        try:
            load_path = path or SETTINGS.ml_model_storage_path
            
            # Load models
            for model_name in self.clustering_models.keys():
                model_path = os.path.join(load_path, f"{model_name}_pattern_model.joblib")
                if os.path.exists(model_path):
                    self.clustering_models[model_name] = joblib.load(model_path)
            
            # Load scalers
            scaler_path = os.path.join(load_path, "pattern_scalers.joblib")
            if os.path.exists(scaler_path):
                self.scalers = joblib.load(scaler_path)
            
            # Load pattern database
            pattern_path = os.path.join(load_path, "pattern_database.json")
            if os.path.exists(pattern_path):
                with open(pattern_path, 'r') as f:
                    self.pattern_database = json.load(f)
            
            self.is_trained = True
            logger.info(f"Pattern recognition models loaded from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
