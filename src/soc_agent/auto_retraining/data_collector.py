"""Data collector for auto-retraining pipeline."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..config import SETTINGS
from ..database import get_db, get_historical_alerts, get_historical_incidents, get_historical_risk_data, get_all_feedback

logger = logging.getLogger(__name__)

class DataCollector:
    """
    Collects and prepares training data for auto-retraining pipeline.
    Handles data collection, preprocessing, and quality validation.
    """

    def __init__(self):
        self.last_collection_time = None
        self.collection_stats = {
            "total_collections": 0,
            "successful_collections": 0,
            "failed_collections": 0,
            "total_data_points": 0
        }

    async def collect_training_data(self, 
                                  data_types: List[str] = None,
                                  time_window_hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collects training data from various sources.
        
        Args:
            data_types: Types of data to collect (alerts, incidents, risk_data, feedback)
            time_window_hours: Time window for data collection in hours
            
        Returns:
            Dict containing collected training data by type
        """
        if data_types is None:
            data_types = ["alerts", "incidents", "risk_data", "feedback"]
        
        training_data = {}
        collection_start = datetime.utcnow()
        
        try:
            with get_db() as db:
                # Collect alerts data
                if "alerts" in data_types:
                    alerts = get_historical_alerts(db, limit=SETTINGS.max_training_data_size)
                    training_data["alerts"] = alerts
                    logger.info(f"Collected {len(alerts)} alerts for training")
                
                # Collect incidents data
                if "incidents" in data_types:
                    incidents = get_historical_incidents(db, limit=SETTINGS.max_training_data_size)
                    training_data["incidents"] = incidents
                    logger.info(f"Collected {len(incidents)} incidents for training")
                
                # Collect risk data
                if "risk_data" in data_types:
                    risk_data = get_historical_risk_data(db, limit=SETTINGS.max_training_data_size)
                    training_data["risk_data"] = risk_data
                    logger.info(f"Collected {len(risk_data)} risk data points for training")
                
                # Collect feedback data
                if "feedback" in data_types:
                    feedback = get_all_feedback(db, limit=SETTINGS.max_training_data_size)
                    training_data["feedback"] = feedback
                    logger.info(f"Collected {len(feedback)} feedback records for training")
            
            # Update collection stats
            self.collection_stats["total_collections"] += 1
            self.collection_stats["successful_collections"] += 1
            total_data_points = sum(len(data) for data in training_data.values())
            self.collection_stats["total_data_points"] += total_data_points
            
            self.last_collection_time = collection_start
            
            logger.info(f"Successfully collected training data: {total_data_points} total data points")
            return training_data
            
        except Exception as e:
            logger.error(f"Error collecting training data: {e}")
            self.collection_stats["failed_collections"] += 1
            return {}

    async def collect_incremental_data(self, 
                                     last_collection_time: datetime,
                                     data_types: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collects only new data since last collection.
        
        Args:
            last_collection_time: Timestamp of last collection
            data_types: Types of data to collect
            
        Returns:
            Dict containing incremental training data
        """
        if data_types is None:
            data_types = ["alerts", "incidents", "risk_data", "feedback"]
        
        incremental_data = {}
        
        try:
            with get_db() as db:
                # Collect new alerts since last collection
                if "alerts" in data_types:
                    # This would need to be implemented in the database layer
                    # to filter by timestamp
                    alerts = get_historical_alerts(db, limit=SETTINGS.max_training_data_size)
                    # Filter by timestamp (simplified - in production, this would be done in SQL)
                    incremental_data["alerts"] = [
                        alert for alert in alerts
                        if datetime.fromisoformat(alert.get("timestamp", "1970-01-01T00:00:00")) > last_collection_time
                    ]
                
                # Similar for other data types...
                # This is simplified - in production, you'd have proper timestamp filtering
                
            logger.info(f"Collected incremental data: {sum(len(data) for data in incremental_data.values())} new data points")
            return incremental_data
            
        except Exception as e:
            logger.error(f"Error collecting incremental data: {e}")
            return {}

    async def get_feedback_count_since_last_retraining(self) -> int:
        """
        Gets the count of feedback records since last retraining.
        
        Returns:
            int: Number of feedback records
        """
        try:
            with get_db() as db:
                # This would need to be implemented with proper timestamp filtering
                # For now, return a placeholder
                feedback = get_all_feedback(db, limit=1000)
                return len(feedback)
        except Exception as e:
            logger.error(f"Error getting feedback count: {e}")
            return 0

    async def validate_data_quality(self, training_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Validates the quality of collected training data.
        
        Args:
            training_data: Collected training data
            
        Returns:
            Dict containing validation results
        """
        validation_results = {
            "is_valid": True,
            "issues": [],
            "data_quality_metrics": {}
        }
        
        try:
            for data_type, data in training_data.items():
                if not data:
                    validation_results["issues"].append(f"No {data_type} data available")
                    continue
                
                # Check data size
                data_size = len(data)
                min_required = SETTINGS.min_training_data_size
                
                if data_size < min_required:
                    validation_results["issues"].append(
                        f"Insufficient {data_type} data: {data_size} < {min_required}"
                    )
                    validation_results["is_valid"] = False
                
                # Check data completeness
                completeness_score = await self._calculate_completeness(data)
                validation_results["data_quality_metrics"][f"{data_type}_completeness"] = completeness_score
                
                if completeness_score < SETTINGS.min_data_completeness:
                    validation_results["issues"].append(
                        f"Low data completeness for {data_type}: {completeness_score:.2f} < {SETTINGS.min_data_completeness}"
                    )
                    validation_results["is_valid"] = False
                
                # Check data freshness
                freshness_score = await self._calculate_freshness(data)
                validation_results["data_quality_metrics"][f"{data_type}_freshness"] = freshness_score
                
                if freshness_score < SETTINGS.min_data_freshness:
                    validation_results["issues"].append(
                        f"Stale data for {data_type}: {freshness_score:.2f} < {SETTINGS.min_data_freshness}"
                    )
                    validation_results["is_valid"] = False
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating data quality: {e}")
            validation_results["is_valid"] = False
            validation_results["issues"].append(f"Validation error: {str(e)}")
            return validation_results

    async def _calculate_completeness(self, data: List[Dict[str, Any]]) -> float:
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

    async def _calculate_freshness(self, data: List[Dict[str, Any]]) -> float:
        """Calculates data freshness score based on timestamps."""
        if not data:
            return 0.0
        
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

    async def preprocess_training_data(self, 
                                     training_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Preprocesses training data for model training.
        
        Args:
            training_data: Raw training data
            
        Returns:
            Dict containing preprocessed training data
        """
        preprocessed_data = {}
        
        try:
            for data_type, data in training_data.items():
                if not data:
                    continue
                
                # Apply data type specific preprocessing
                if data_type == "alerts":
                    preprocessed_data[data_type] = await self._preprocess_alerts(data)
                elif data_type == "incidents":
                    preprocessed_data[data_type] = await self._preprocess_incidents(data)
                elif data_type == "risk_data":
                    preprocessed_data[data_type] = await self._preprocess_risk_data(data)
                elif data_type == "feedback":
                    preprocessed_data[data_type] = await self._preprocess_feedback(data)
                else:
                    preprocessed_data[data_type] = data
            
            logger.info("Training data preprocessing completed")
            return preprocessed_data
            
        except Exception as e:
            logger.error(f"Error preprocessing training data: {e}")
            return training_data

    async def _preprocess_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preprocesses alert data."""
        preprocessed = []
        
        for alert in alerts:
            # Add derived features
            processed_alert = {
                **alert,
                "severity_numeric": self._severity_to_numeric(alert.get("severity", "LOW")),
                "has_description": bool(alert.get("description", "")),
                "event_count": alert.get("event_count", 1),
                "is_weekend": self._is_weekend(alert.get("timestamp", "")),
                "is_business_hours": self._is_business_hours(alert.get("timestamp", ""))
            }
            preprocessed.append(processed_alert)
        
        return preprocessed

    async def _preprocess_incidents(self, incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preprocesses incident data."""
        preprocessed = []
        
        for incident in incidents:
            processed_incident = {
                **incident,
                "severity_numeric": self._severity_to_numeric(incident.get("severity", "LOW")),
                "duration_hours": self._calculate_duration_hours(incident),
                "has_resolution": bool(incident.get("resolution", "")),
                "is_auto_classified": incident.get("auto_classified", False)
            }
            preprocessed.append(processed_incident)
        
        return preprocessed

    async def _preprocess_risk_data(self, risk_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preprocesses risk data."""
        preprocessed = []
        
        for risk in risk_data:
            processed_risk = {
                **risk,
                "risk_level_numeric": self._risk_level_to_numeric(risk.get("risk_level", "LOW")),
                "has_mitigation": bool(risk.get("mitigation", "")),
                "is_verified": risk.get("verified", False)
            }
            preprocessed.append(processed_risk)
        
        return preprocessed

    async def _preprocess_feedback(self, feedback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preprocesses feedback data."""
        preprocessed = []
        
        for fb in feedback:
            processed_feedback = {
                **fb,
                "feedback_positive": fb.get("is_correct", False),
                "has_explanation": bool(fb.get("explanation", "")),
                "confidence_score": fb.get("confidence", 0.5)
            }
            preprocessed.append(processed_feedback)
        
        return preprocessed

    def _severity_to_numeric(self, severity: str) -> int:
        """Converts severity string to numeric value."""
        severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        return severity_map.get(severity.upper(), 1)

    def _risk_level_to_numeric(self, risk_level: str) -> int:
        """Converts risk level string to numeric value."""
        risk_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        return risk_map.get(risk_level.upper(), 1)

    def _is_weekend(self, timestamp_str: str) -> bool:
        """Checks if timestamp is on weekend."""
        try:
            dt = datetime.fromisoformat(timestamp_str)
            return dt.weekday() >= 5  # Saturday = 5, Sunday = 6
        except:
            return False

    def _is_business_hours(self, timestamp_str: str) -> bool:
        """Checks if timestamp is during business hours (9 AM - 5 PM)."""
        try:
            dt = datetime.fromisoformat(timestamp_str)
            return 9 <= dt.hour < 17 and dt.weekday() < 5
        except:
            return False

    def _calculate_duration_hours(self, incident: Dict[str, Any]) -> float:
        """Calculates incident duration in hours."""
        try:
            start_time = datetime.fromisoformat(incident.get("start_time", ""))
            end_time = datetime.fromisoformat(incident.get("end_time", ""))
            return (end_time - start_time).total_seconds() / 3600
        except:
            return 0.0

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Gets data collection statistics."""
        return {
            **self.collection_stats,
            "last_collection_time": self.last_collection_time.isoformat() if self.last_collection_time else None
        }
