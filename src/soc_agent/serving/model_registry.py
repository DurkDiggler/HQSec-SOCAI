"""Model registry for managing ML model versions and deployments."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import mlflow
import mlflow.sklearn

from ..config import SETTINGS

logger = logging.getLogger(__name__)

class ModelRegistry:
    """
    Model registry for managing ML model versions, metadata, and deployments.
    Integrates with MLflow for model tracking and versioning.
    """

    def __init__(self, registry_path: str = None):
        self.registry_path = registry_path or SETTINGS.ml_model_storage_path
        self.models: Dict[str, Dict[str, Any]] = {}
        self.deployments: Dict[str, str] = {}  # model_name -> version
        
        # Configure MLflow
        mlflow.set_tracking_uri(SETTINGS.mlflow_tracking_uri)
        if SETTINGS.mlflow_registry_uri:
            mlflow.set_registry_uri(SETTINGS.mlflow_registry_uri)

    async def register_model(self, 
                            model_name: str,
                            model_object: Any,
                            model_type: str = "sklearn",
                            version: str = None,
                            description: str = None,
                            metrics: Dict[str, float] = None,
                            parameters: Dict[str, Any] = None,
                            tags: Dict[str, str] = None) -> str:
        """
        Registers a new model version in the registry.
        
        Args:
            model_name: Name of the model
            model_object: Trained model object
            model_type: Type of model (sklearn, tensorflow, etc.)
            version: Model version (auto-generated if None)
            description: Model description
            metrics: Model performance metrics
            parameters: Model parameters
            tags: Model tags
            
        Returns:
            str: Model version
        """
        try:
            # Generate version if not provided
            if not version:
                version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Create model metadata
            model_metadata = {
                "model_name": model_name,
                "version": version,
                "model_type": model_type,
                "description": description or f"Model {model_name} version {version}",
                "created_at": datetime.utcnow().isoformat(),
                "metrics": metrics or {},
                "parameters": parameters or {},
                "tags": tags or {},
                "status": "registered"
            }
            
            # Calculate model hash for integrity checking
            model_hash = await self._calculate_model_hash(model_object)
            model_metadata["model_hash"] = model_hash
            
            # Save model to local storage
            model_path = await self._save_model_locally(model_name, version, model_object)
            model_metadata["local_path"] = model_path
            
            # Register with MLflow
            if SETTINGS.mlflow_tracking_uri:
                await self._register_with_mlflow(model_name, model_object, model_metadata)
            
            # Store in local registry
            registry_key = f"{model_name}_{version}"
            self.models[registry_key] = model_metadata
            
            logger.info(f"Model {model_name} version {version} registered successfully")
            return version
            
        except Exception as e:
            logger.error(f"Failed to register model {model_name}: {e}")
            raise

    async def _calculate_model_hash(self, model_object: Any) -> str:
        """Calculates hash of model object for integrity checking."""
        try:
            # Serialize model to bytes
            model_bytes = joblib.dumps(model_object)
            # Calculate SHA-256 hash
            return hashlib.sha256(model_bytes).hexdigest()
        except Exception as e:
            logger.warning(f"Could not calculate model hash: {e}")
            return "unknown"

    async def _save_model_locally(self, model_name: str, version: str, model_object: Any) -> str:
        """Saves model to local storage."""
        model_dir = Path(self.registry_path) / model_name / version
        model_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = model_dir / "model.joblib"
        joblib.dump(model_object, model_path)
        
        return str(model_path)

    async def _register_with_mlflow(self, model_name: str, model_object: Any, metadata: Dict[str, Any]):
        """Registers model with MLflow."""
        try:
            with mlflow.start_run() as run:
                # Log parameters
                if metadata["parameters"]:
                    mlflow.log_params(metadata["parameters"])
                
                # Log metrics
                if metadata["metrics"]:
                    mlflow.log_metrics(metadata["metrics"])
                
                # Log tags
                if metadata["tags"]:
                    mlflow.set_tags(metadata["tags"])
                
                # Log model
                mlflow.sklearn.log_model(model_object, "model")
                
                # Register model
                model_uri = f"runs:/{run.info.run_id}/model"
                mlflow.register_model(model_uri, f"soc-agent-{model_name}")
                
                logger.info(f"Model {model_name} registered with MLflow")
                
        except Exception as e:
            logger.error(f"Failed to register with MLflow: {e}")

    async def get_model(self, model_name: str, version: str = None) -> Optional[Any]:
        """
        Retrieves a model from the registry.
        
        Args:
            model_name: Name of the model
            version: Model version (latest if None)
            
        Returns:
            Model object or None if not found
        """
        try:
            if not version:
                version = await self.get_latest_version(model_name)
            
            if not version:
                return None
            
            registry_key = f"{model_name}_{version}"
            if registry_key not in self.models:
                logger.warning(f"Model {model_name} version {version} not found in registry")
                return None
            
            model_metadata = self.models[registry_key]
            model_path = model_metadata["local_path"]
            
            # Load model
            model = joblib.load(model_path)
            
            # Verify model integrity
            current_hash = await self._calculate_model_hash(model)
            stored_hash = model_metadata.get("model_hash", "")
            
            if stored_hash != "unknown" and current_hash != stored_hash:
                logger.warning(f"Model integrity check failed for {model_name} version {version}")
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to get model {model_name} version {version}: {e}")
            return None

    async def get_latest_version(self, model_name: str) -> Optional[str]:
        """Gets the latest version of a model."""
        try:
            model_versions = [
                key.split("_", 1)[1] for key in self.models.keys()
                if key.startswith(f"{model_name}_")
            ]
            
            if not model_versions:
                return None
            
            # Sort versions (assuming timestamp format)
            model_versions.sort(reverse=True)
            return model_versions[0]
            
        except Exception as e:
            logger.error(f"Failed to get latest version for {model_name}: {e}")
            return None

    async def list_models(self) -> List[Dict[str, Any]]:
        """Lists all registered models."""
        models_list = []
        
        for registry_key, metadata in self.models.items():
            model_name, version = registry_key.split("_", 1)
            
            models_list.append({
                "model_name": model_name,
                "version": version,
                "model_type": metadata["model_type"],
                "description": metadata["description"],
                "created_at": metadata["created_at"],
                "status": metadata["status"],
                "metrics": metadata["metrics"],
                "tags": metadata["tags"]
            })
        
        return models_list

    async def list_model_versions(self, model_name: str) -> List[Dict[str, Any]]:
        """Lists all versions of a specific model."""
        versions = []
        
        for registry_key, metadata in self.models.items():
            if registry_key.startswith(f"{model_name}_"):
                version = registry_key.split("_", 1)[1]
                versions.append({
                    "version": version,
                    "model_type": metadata["model_type"],
                    "description": metadata["description"],
                    "created_at": metadata["created_at"],
                    "status": metadata["status"],
                    "metrics": metadata["metrics"],
                    "tags": metadata["tags"]
                })
        
        # Sort by creation time (newest first)
        versions.sort(key=lambda x: x["created_at"], reverse=True)
        return versions

    async def deploy_model(self, model_name: str, version: str, environment: str = "production") -> bool:
        """
        Deploys a model to a specific environment.
        
        Args:
            model_name: Name of the model
            version: Model version
            environment: Deployment environment
            
        Returns:
            bool: True if deployment successful
        """
        try:
            registry_key = f"{model_name}_{version}"
            if registry_key not in self.models:
                logger.error(f"Model {model_name} version {version} not found")
                return False
            
            # Update model status
            self.models[registry_key]["status"] = f"deployed_{environment}"
            self.models[registry_key]["deployed_at"] = datetime.utcnow().isoformat()
            self.models[registry_key]["environment"] = environment
            
            # Update deployment tracking
            self.deployments[model_name] = version
            
            logger.info(f"Model {model_name} version {version} deployed to {environment}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy model {model_name} version {version}: {e}")
            return False

    async def undeploy_model(self, model_name: str) -> bool:
        """Undeploys a model from all environments."""
        try:
            if model_name not in self.deployments:
                logger.warning(f"Model {model_name} is not deployed")
                return False
            
            version = self.deployments[model_name]
            registry_key = f"{model_name}_{version}"
            
            if registry_key in self.models:
                self.models[registry_key]["status"] = "registered"
                self.models[registry_key]["undeployed_at"] = datetime.utcnow().isoformat()
            
            del self.deployments[model_name]
            
            logger.info(f"Model {model_name} undeployed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to undeploy model {model_name}: {e}")
            return False

    async def get_deployed_model(self, model_name: str) -> Optional[Any]:
        """Gets the currently deployed model."""
        if model_name not in self.deployments:
            return None
        
        version = self.deployments[model_name]
        return await self.get_model(model_name, version)

    async def get_model_metadata(self, model_name: str, version: str) -> Optional[Dict[str, Any]]:
        """Gets metadata for a specific model version."""
        registry_key = f"{model_name}_{version}"
        return self.models.get(registry_key)

    async def update_model_metadata(self, 
                                   model_name: str, 
                                   version: str, 
                                   updates: Dict[str, Any]) -> bool:
        """Updates metadata for a model version."""
        try:
            registry_key = f"{model_name}_{version}"
            if registry_key not in self.models:
                return False
            
            self.models[registry_key].update(updates)
            self.models[registry_key]["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Updated metadata for {model_name} version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metadata for {model_name} version {version}: {e}")
            return False

    async def delete_model(self, model_name: str, version: str) -> bool:
        """Deletes a model version from the registry."""
        try:
            registry_key = f"{model_name}_{version}"
            if registry_key not in self.models:
                return False
            
            # Check if model is deployed
            if model_name in self.deployments and self.deployments[model_name] == version:
                logger.error(f"Cannot delete deployed model {model_name} version {version}")
                return False
            
            # Remove from registry
            del self.models[registry_key]
            
            # Remove local files
            model_metadata = self.models.get(registry_key, {})
            local_path = model_metadata.get("local_path")
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
            
            logger.info(f"Deleted model {model_name} version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete model {model_name} version {version}: {e}")
            return False

    async def get_registry_status(self) -> Dict[str, Any]:
        """Gets the current status of the model registry."""
        return {
            "total_models": len(set(key.split("_", 1)[0] for key in self.models.keys())),
            "total_versions": len(self.models),
            "deployed_models": len(self.deployments),
            "deployments": self.deployments,
            "registry_path": self.registry_path,
            "mlflow_configured": bool(SETTINGS.mlflow_tracking_uri)
        }
