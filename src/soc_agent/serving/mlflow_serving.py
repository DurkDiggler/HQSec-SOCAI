"""MLflow model serving integration for ML model deployment."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import mlflow
import mlflow.sklearn
import mlflow.tensorflow
import requests

from ..config import SETTINGS

logger = logging.getLogger(__name__)

class MLflowModelServer:
    """
    MLflow model serving integration for deploying and managing ML models.
    Handles model registry, versioning, and serving.
    """

    def __init__(self, 
                 tracking_uri: str = None,
                 registry_uri: str = None,
                 serving_port: int = 5000,
                 serving_host: str = "localhost"):
        self.tracking_uri = tracking_uri or SETTINGS.mlflow_tracking_uri
        self.registry_uri = registry_uri or SETTINGS.mlflow_registry_uri
        self.serving_port = serving_port
        self.serving_host = serving_host
        self.serving_process = None
        self.base_url = f"http://{serving_host}:{serving_port}"
        
        # Configure MLflow
        mlflow.set_tracking_uri(self.tracking_uri)
        if self.registry_uri:
            mlflow.set_registry_uri(self.registry_uri)

    async def start_serving(self):
        """Starts the MLflow model serving server."""
        if self.serving_process and self.serving_process.poll() is None:
            logger.info("MLflow model serving is already running")
            return

        try:
            # Start MLflow model serving
            cmd = [
                "mlflow", "models", "serve",
                "--model-uri", f"models:/soc-agent-models/latest",
                "--port", str(self.serving_port),
                "--host", self.serving_host
            ]

            logger.info(f"Starting MLflow model serving with command: {' '.join(cmd)}")
            self.serving_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for server to start
            await self._wait_for_server_ready()
            logger.info("MLflow model serving started successfully")

        except Exception as e:
            logger.error(f"Failed to start MLflow model serving: {e}")
            raise

    async def _wait_for_server_ready(self, timeout: int = 60):
        """Waits for MLflow model serving server to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    logger.info("MLflow model serving is ready")
                    return
            except requests.exceptions.RequestException:
                pass
            
            await asyncio.sleep(1)
        
        raise TimeoutError("MLflow model serving failed to start within timeout")

    async def stop_serving(self):
        """Stops the MLflow model serving server."""
        if self.serving_process:
            self.serving_process.terminate()
            self.serving_process.wait()
            self.serving_process = None
            logger.info("MLflow model serving stopped")

    async def log_model(self, 
                       model, 
                       model_name: str,
                       model_type: str = "sklearn",
                       metrics: Dict[str, float] = None,
                       parameters: Dict[str, Any] = None,
                       tags: Dict[str, str] = None) -> str:
        """
        Logs a model to MLflow tracking.
        
        Args:
            model: Trained model object
            model_name: Name of the model
            model_type: Type of model (sklearn, tensorflow, etc.)
            metrics: Model performance metrics
            parameters: Model parameters
            tags: Model tags
            
        Returns:
            str: Model URI
        """
        try:
            with mlflow.start_run() as run:
                # Log parameters
                if parameters:
                    mlflow.log_params(parameters)
                
                # Log metrics
                if metrics:
                    mlflow.log_metrics(metrics)
                
                # Log tags
                if tags:
                    mlflow.set_tags(tags)
                
                # Log model based on type
                if model_type == "sklearn":
                    mlflow.sklearn.log_model(model, "model")
                elif model_type == "tensorflow":
                    mlflow.tensorflow.log_model(model, "model")
                else:
                    # Generic model logging
                    mlflow.log_model(model, "model")
                
                # Register model
                model_uri = f"runs:/{run.info.run_id}/model"
                mlflow.register_model(model_uri, f"soc-agent-{model_name}")
                
                logger.info(f"Model {model_name} logged and registered successfully")
                return model_uri

        except Exception as e:
            logger.error(f"Failed to log model {model_name}: {e}")
            raise

    async def deploy_model(self, 
                          model_name: str, 
                          version: str = "latest",
                          stage: str = "Production") -> bool:
        """
        Deploys a model from the registry to serving.
        
        Args:
            model_name: Name of the model
            version: Model version
            stage: Deployment stage
            
        Returns:
            bool: True if deployment successful
        """
        try:
            # Transition model to specified stage
            client = mlflow.tracking.MlflowClient()
            client.transition_model_version_stage(
                name=f"soc-agent-{model_name}",
                version=version,
                stage=stage
            )
            
            logger.info(f"Model {model_name} v{version} deployed to {stage} stage")
            return True

        except Exception as e:
            logger.error(f"Failed to deploy model {model_name}: {e}")
            return False

    async def predict(self, 
                     model_name: str, 
                     inputs: Dict[str, Any],
                     version: str = "latest") -> Dict[str, Any]:
        """
        Makes a prediction using the deployed model.
        
        Args:
            model_name: Name of the model
            inputs: Input data for prediction
            version: Model version
            
        Returns:
            Dict containing prediction results
        """
        try:
            # Load model from registry
            model_uri = f"models:/soc-agent-{model_name}/{version}"
            model = mlflow.sklearn.load_model(model_uri)
            
            # Make prediction
            if isinstance(inputs, dict):
                # Convert dict to array format expected by sklearn
                input_array = [[inputs.get(key, 0) for key in sorted(inputs.keys())]]
            else:
                input_array = inputs
            
            prediction = model.predict(input_array)
            
            # Get prediction probabilities if available
            result = {"prediction": prediction.tolist()}
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(input_array)
                result["probabilities"] = probabilities.tolist()
            
            return result

        except Exception as e:
            logger.error(f"Prediction failed for model {model_name}: {e}")
            raise

    async def get_model_versions(self, model_name: str) -> List[Dict[str, Any]]:
        """
        Gets all versions of a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of model version information
        """
        try:
            client = mlflow.tracking.MlflowClient()
            versions = client.get_latest_versions(f"soc-agent-{model_name}")
            
            return [
                {
                    "version": v.version,
                    "stage": v.current_stage,
                    "creation_timestamp": v.creation_timestamp,
                    "last_updated_timestamp": v.last_updated_timestamp
                }
                for v in versions
            ]

        except Exception as e:
            logger.error(f"Failed to get model versions for {model_name}: {e}")
            return []

    async def get_model_info(self, model_name: str, version: str = "latest") -> Dict[str, Any]:
        """
        Gets information about a specific model version.
        
        Args:
            model_name: Name of the model
            version: Model version
            
        Returns:
            Dict containing model information
        """
        try:
            client = mlflow.tracking.MlflowClient()
            model_version = client.get_model_version(f"soc-agent-{model_name}", version)
            
            return {
                "name": model_version.name,
                "version": model_version.version,
                "stage": model_version.current_stage,
                "description": model_version.description,
                "creation_timestamp": model_version.creation_timestamp,
                "last_updated_timestamp": model_version.last_updated_timestamp,
                "run_id": model_version.run_id
            }

        except Exception as e:
            logger.error(f"Failed to get model info for {model_name}: {e}")
            return {}

    async def health_check(self) -> bool:
        """Checks if MLflow model serving is healthy."""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.create_task(self.stop_serving())
