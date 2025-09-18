"""Feature engineering for ML models."""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
import hashlib

from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from sklearn.impute import SimpleImputer
from feature_engine.categorical_encoders import OneHotEncoder as FEOneHotEncoder
from feature_engine.categorical_encoders import TargetEncoder
from feature_engine.imputation import CategoricalImputer, MeanMedianImputer

from ..config import SETTINGS

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Feature engineering for ML models."""
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.vectorizers = {}
        self.feature_selectors = {}
        self.imputers = {}
        self.feature_names = []
        self.feature_importance = {}
        
        # Initialize feature engineering components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize feature engineering components."""
        # Scalers
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler(),
            'robust': StandardScaler()
        }
        
        # Encoders
        self.encoders = {
            'label': LabelEncoder(),
            'onehot': OneHotEncoder(handle_unknown='ignore'),
            'target': TargetEncoder()
        }
        
        # Vectorizers
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
        
        # Feature selectors
        self.feature_selectors = {
            'kbest': SelectKBest(score_func=f_classif, k=50),
            'mutual_info': SelectKBest(score_func=mutual_info_classif, k=50)
        }
        
        # Imputers
        self.imputers = {
            'numeric': SimpleImputer(strategy='mean'),
            'categorical': SimpleImputer(strategy='most_frequent')
        }
    
    def engineer_features(self, data: pd.DataFrame, target_column: str = None) -> Tuple[np.ndarray, List[str]]:
        """Engineer features from raw data."""
        try:
            logger.info("Starting feature engineering...")
            
            # Create a copy of the data
            df = data.copy()
            
            # Basic feature engineering
            df = self._add_basic_features(df)
            
            # Text feature engineering
            df = self._add_text_features(df)
            
            # Time feature engineering
            df = self._add_time_features(df)
            
            # Network feature engineering
            df = self._add_network_features(df)
            
            # Categorical feature engineering
            df = self._add_categorical_features(df)
            
            # Numeric feature engineering
            df = self._add_numeric_features(df)
            
            # Feature selection
            if target_column and target_column in df.columns:
                X, y = self._prepare_features_and_target(df, target_column)
                X_selected, selected_features = self._select_features(X, y)
                return X_selected, selected_features
            else:
                X = self._prepare_features(df)
                return X, self.feature_names
            
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            return np.array([]), []
    
    def _add_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic features."""
        try:
            # Message length
            if 'message' in df.columns:
                df['message_length'] = df['message'].astype(str).str.len()
                df['message_word_count'] = df['message'].astype(str).str.split().str.len()
                df['message_char_count'] = df['message'].astype(str).str.len()
            
            # Event type features
            if 'event_type' in df.columns:
                df['event_type_length'] = df['event_type'].astype(str).str.len()
                df['event_type_word_count'] = df['event_type'].astype(str).str.split().str.len()
            
            # Source features
            if 'source' in df.columns:
                df['source_length'] = df['source'].astype(str).str.len()
                df['source_word_count'] = df['source'].astype(str).str.split().str.len()
            
            return df
            
        except Exception as e:
            logger.error(f"Basic feature engineering failed: {e}")
            return df
    
    def _add_text_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add text-based features."""
        try:
            # Combine text fields
            if 'message' in df.columns and 'event_type' in df.columns:
                df['combined_text'] = df['message'].astype(str) + ' ' + df['event_type'].astype(str)
            elif 'message' in df.columns:
                df['combined_text'] = df['message'].astype(str)
            else:
                df['combined_text'] = ''
            
            # Text statistics
            df['text_uppercase_ratio'] = df['combined_text'].str.count(r'[A-Z]') / df['combined_text'].str.len().replace(0, 1)
            df['text_lowercase_ratio'] = df['combined_text'].str.count(r'[a-z]') / df['combined_text'].str.len().replace(0, 1)
            df['text_digit_ratio'] = df['combined_text'].str.count(r'[0-9]') / df['combined_text'].str.len().replace(0, 1)
            df['text_special_ratio'] = df['combined_text'].str.count(r'[^a-zA-Z0-9\s]') / df['combined_text'].str.len().replace(0, 1)
            
            # Common security keywords
            security_keywords = [
                'attack', 'malware', 'virus', 'trojan', 'exploit', 'breach',
                'intrusion', 'unauthorized', 'suspicious', 'anomaly', 'threat'
            ]
            
            for keyword in security_keywords:
                df[f'contains_{keyword}'] = df['combined_text'].str.contains(keyword, case=False, na=False).astype(int)
            
            # Error patterns
            error_patterns = ['error', 'failed', 'exception', 'timeout', 'denied']
            for pattern in error_patterns:
                df[f'contains_{pattern}'] = df['combined_text'].str.contains(pattern, case=False, na=False).astype(int)
            
            return df
            
        except Exception as e:
            logger.error(f"Text feature engineering failed: {e}")
            return df
    
    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features."""
        try:
            # Parse timestamp
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                
                # Extract time components
                df['hour'] = df['timestamp'].dt.hour
                df['day_of_week'] = df['timestamp'].dt.dayofweek
                df['day_of_month'] = df['timestamp'].dt.day
                df['month'] = df['timestamp'].dt.month
                df['year'] = df['timestamp'].dt.year
                
                # Time-based features
                df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
                df['is_off_hours'] = ((df['hour'] < 6) | (df['hour'] > 22)).astype(int)
                df['is_business_hours'] = ((df['hour'] >= 9) & (df['hour'] <= 17) & (df['day_of_week'] < 5)).astype(int)
                
                # Time since last event (if multiple events)
                df['time_since_last'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
                
            return df
            
        except Exception as e:
            logger.error(f"Time feature engineering failed: {e}")
            return df
    
    def _add_network_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add network-based features."""
        try:
            if 'ip' in df.columns:
                # IP address features
                df['ip_length'] = df['ip'].astype(str).str.len()
                df['ip_dot_count'] = df['ip'].astype(str).str.count(r'\.')
                df['ip_colon_count'] = df['ip'].astype(str).str.count(r':')
                
                # IP type classification
                df['is_ipv4'] = df['ip'].astype(str).str.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$').astype(int)
                df['is_ipv6'] = df['ip'].astype(str).str.contains(':').astype(int)
                df['is_localhost'] = df['ip'].astype(str).str.contains('127\.0\.0\.1|localhost').astype(int)
                
                # Internal IP detection
                df['is_internal_ip'] = df['ip'].astype(str).str.match(r'^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)').astype(int)
                
                # IP hash for anonymization
                df['ip_hash'] = df['ip'].astype(str).apply(lambda x: hashlib.md5(x.encode()).hexdigest()[:8])
                
                # Port features (if available)
                if 'port' in df.columns:
                    df['port'] = pd.to_numeric(df['port'], errors='coerce')
                    df['is_well_known_port'] = ((df['port'] >= 0) & (df['port'] <= 1023)).astype(int)
                    df['is_registered_port'] = ((df['port'] >= 1024) & (df['port'] <= 49151)).astype(int)
                    df['is_dynamic_port'] = ((df['port'] >= 49152) & (df['port'] <= 65535)).astype(int)
            
            return df
            
        except Exception as e:
            logger.error(f"Network feature engineering failed: {e}")
            return df
    
    def _add_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add categorical features."""
        try:
            # Severity encoding
            if 'severity' in df.columns:
                severity_mapping = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
                df['severity_numeric'] = df['severity'].map(severity_mapping).fillna(2)
            
            # Event type features
            if 'event_type' in df.columns:
                df['event_type_category'] = df['event_type'].astype(str).str.split('_').str[0]
                df['event_type_subcategory'] = df['event_type'].astype(str).str.split('_').str[1:].str.join('_')
            
            # Source features
            if 'source' in df.columns:
                df['source_type'] = df['source'].astype(str).str.split('_').str[0]
                df['source_instance'] = df['source'].astype(str).str.split('_').str[1:].str.join('_')
            
            # User features
            if 'user' in df.columns:
                df['user_length'] = df['user'].astype(str).str.len()
                df['user_has_domain'] = df['user'].astype(str).str.contains('@').astype(int)
                df['user_domain'] = df['user'].astype(str).str.split('@').str[1]
            
            return df
            
        except Exception as e:
            logger.error(f"Categorical feature engineering failed: {e}")
            return df
    
    def _add_numeric_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add numeric features."""
        try:
            # Count features
            if 'ip' in df.columns:
                df['unique_ip_count'] = df.groupby('timestamp')['ip'].transform('nunique')
            
            if 'user' in df.columns:
                df['unique_user_count'] = df.groupby('timestamp')['user'].transform('nunique')
            
            if 'source' in df.columns:
                df['unique_source_count'] = df.groupby('timestamp')['source'].transform('nunique')
            
            # Frequency features
            if 'ip' in df.columns:
                df['ip_frequency'] = df.groupby('ip')['ip'].transform('count')
            
            if 'user' in df.columns:
                df['user_frequency'] = df.groupby('user')['user'].transform('count')
            
            if 'source' in df.columns:
                df['source_frequency'] = df.groupby('source')['source'].transform('count')
            
            # Rolling statistics
            if 'timestamp' in df.columns:
                df = df.sort_values('timestamp')
                df['rolling_event_count'] = df.rolling(window=5, min_periods=1)['timestamp'].count()
                df['rolling_ip_count'] = df.rolling(window=5, min_periods=1)['ip'].nunique()
            
            return df
            
        except Exception as e:
            logger.error(f"Numeric feature engineering failed: {e}")
            return df
    
    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features for ML models."""
        try:
            # Select numeric columns
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Select categorical columns
            categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
            
            # Prepare numeric features
            if numeric_columns:
                numeric_data = df[numeric_columns].fillna(0)
                # Scale numeric features
                if 'standard' in self.scalers:
                    numeric_data = self.scalers['standard'].fit_transform(numeric_data)
            else:
                numeric_data = np.zeros((len(df), 1))
            
            # Prepare categorical features
            if categorical_columns:
                categorical_data = df[categorical_columns].fillna('unknown')
                # Encode categorical features
                encoded_data = []
                for col in categorical_columns:
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
                    categorical_encoded = np.zeros((len(df), 1))
            else:
                categorical_encoded = np.zeros((len(df), 1))
            
            # Combine features
            features = np.column_stack([numeric_data, categorical_encoded])
            
            # Store feature names
            self.feature_names = numeric_columns + [f"cat_{i}" for i in range(categorical_encoded.shape[1])]
            
            return features
            
        except Exception as e:
            logger.error(f"Feature preparation failed: {e}")
            return np.zeros((len(df), 1))
    
    def _prepare_features_and_target(self, df: pd.DataFrame, target_column: str) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and target for supervised learning."""
        try:
            # Prepare features
            X = self._prepare_features(df)
            
            # Prepare target
            y = df[target_column].values
            
            return X, y
            
        except Exception as e:
            logger.error(f"Feature and target preparation failed: {e}")
            return np.array([]), np.array([])
    
    def _select_features(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """Select most important features."""
        try:
            if X.shape[1] <= 50:
                return X, self.feature_names
            
            # Use mutual information for feature selection
            if 'mutual_info' in self.feature_selectors:
                selector = self.feature_selectors['mutual_info']
                X_selected = selector.fit_transform(X, y)
                
                # Get selected feature names
                selected_indices = selector.get_support(indices=True)
                selected_features = [self.feature_names[i] for i in selected_indices]
                
                return X_selected, selected_features
            else:
                return X, self.feature_names
                
        except Exception as e:
            logger.error(f"Feature selection failed: {e}")
            return X, self.feature_names
    
    def get_feature_importance(self, model, feature_names: List[str]) -> Dict[str, float]:
        """Get feature importance from trained model."""
        try:
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
                return dict(zip(feature_names, importance))
            elif hasattr(model, 'coef_'):
                importance = np.abs(model.coef_[0])
                return dict(zip(feature_names, importance))
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Feature importance extraction failed: {e}")
            return {}
    
    def save_components(self, path: str = None) -> bool:
        """Save feature engineering components."""
        try:
            save_path = path or SETTINGS.ml_model_storage_path
            os.makedirs(save_path, exist_ok=True)
            
            # Save scalers
            scaler_path = os.path.join(save_path, 'feature_scalers.joblib')
            joblib.dump(self.scalers, scaler_path)
            
            # Save encoders
            encoder_path = os.path.join(save_path, 'feature_encoders.joblib')
            joblib.dump(self.encoders, encoder_path)
            
            # Save vectorizers
            vectorizer_path = os.path.join(save_path, 'feature_vectorizers.joblib')
            joblib.dump(self.vectorizers, vectorizer_path)
            
            # Save feature names
            names_path = os.path.join(save_path, 'feature_names.json')
            with open(names_path, 'w') as f:
                json.dump(self.feature_names, f)
            
            logger.info(f"Feature engineering components saved to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save feature components: {e}")
            return False
    
    def load_components(self, path: str = None) -> bool:
        """Load feature engineering components."""
        try:
            load_path = path or SETTINGS.ml_model_storage_path
            
            # Load scalers
            scaler_path = os.path.join(load_path, 'feature_scalers.joblib')
            if os.path.exists(scaler_path):
                self.scalers = joblib.load(scaler_path)
            
            # Load encoders
            encoder_path = os.path.join(load_path, 'feature_encoders.joblib')
            if os.path.exists(encoder_path):
                self.encoders = joblib.load(encoder_path)
            
            # Load vectorizers
            vectorizer_path = os.path.join(load_path, 'feature_vectorizers.joblib')
            if os.path.exists(vectorizer_path):
                self.vectorizers = joblib.load(vectorizer_path)
            
            # Load feature names
            names_path = os.path.join(load_path, 'feature_names.json')
            if os.path.exists(names_path):
                with open(names_path, 'r') as f:
                    self.feature_names = json.load(f)
            
            logger.info(f"Feature engineering components loaded from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load feature components: {e}")
            return False
