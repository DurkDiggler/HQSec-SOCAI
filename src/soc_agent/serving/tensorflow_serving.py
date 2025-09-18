"""TensorFlow Serving integration for model deployment."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import numpy as np

from ..config import SETTINGS

logger = logging.getLogger(__name__)

class TensorFlowModelServer:
    """
    TensorFlow Serving integration for deploying and serving ML models.
    Handles model deployment, versioning, and inference requests.
    """

    def __init__(self, 
                 serving_port: int = 8500,
                 grpc_port: int = 8501,
                 model_base_path: str = None,
                 serving_host: str = "localhost"):
        self.serving_port = serving_port
        self.grpc_port = grpc_port
        self.model_base_path = model_base_path or SETTINGS.tf_serving_model_path
        self.serving_host = serving_host
        self.serving_process = None
        self.base_url = f"http://{serving_host}:{serving_port}"
        self.grpc_url = f"{serving_host}:{grpc_port}"

    async def start_serving(self):
        """Starts the TensorFlow Serving server."""
        if self.serving_process and self.serving_process.poll() is None:
            logger.info("TensorFlow Serving is already running")
            return

        try:
            # Ensure model directory exists
            Path(self.model_base_path).mkdir(parents=True, exist_ok=True)

            # Start TensorFlow Serving
            cmd = [
                "tensorflow_model_server",
                "--port", str(self.serving_port),
                "--grpc_port", str(self.grpc_port),
                "--model_base_path", self.model_base_path,
                "--model_config_file", f"{self.model_base_path}/models.config",
                "--enable_batching", "true",
                "--batching_parameters_file", f"{self.model_base_path}/batching.config"
            ]

            logger.info(f"Starting TensorFlow Serving with command: {' '.join(cmd)}")
            self.serving_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for server to start
            await self._wait_for_server_ready()
            logger.info("TensorFlow Serving started successfully")

        except Exception as e:
            logger.error(f"Failed to start TensorFlow Serving: {e}")
            raise

    async def _wait_for_server_ready(self, timeout: int = 60):
        """Waits for TensorFlow Serving server to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/v1/models")
                if response.status_code == 200:
                    logger.info("TensorFlow Serving is ready")
                    return
            except requests.exceptions.RequestException:
                pass
            
            await asyncio.sleep(1)
        
        raise TimeoutError("TensorFlow Serving failed to start within timeout")

    async def stop_serving(self):
        """Stops the TensorFlow Serving server."""
        if self.serving_process:
            self.serving_process.terminate()
            self.serving_process.wait()
            self.serving_process = None
            logger.info("TensorFlow Serving stopped")

    async def deploy_model(self, 
                          model_name: str, 
                          model_version: str,
                          model_path: str,
                          signature_name: str = "serving_default") -> bool:
        """
        Deploys a TensorFlow model to the serving server.
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            model_path: Path to the saved model directory
            signature_name: Signature name for inference
            
        Returns:
            bool: True if deployment successful
        """
        try:
            # Create model directory structure
            model_dir = Path(self.model_base_path) / model_name / model_version
            model_dir.mkdir(parents=True, exist_ok=True)

            # Copy model files (in production, this would be more sophisticated)
            import shutil
            shutil.copytree(model_path, model_dir, dirs_exist_ok=True)

            # Update models.config
            await self._update_models_config()

            # Reload models
            await self._reload_models()

            logger.info(f"Model {model_name} v{model_version} deployed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to deploy model {model_name}: {e}")
            return False

    async def _update_models_config(self):
        """Updates the models.config file with current model configurations."""
        config_path = Path(self.model_base_path) / "models.config"
        
        # This would be more sophisticated in production
        config = {
            "model_config_list": []
        }
        
        # Scan for deployed models
        for model_dir in Path(self.model_base_path).iterdir():
            if model_dir.is_dir():
                for version_dir in model_dir.iterdir():
                    if version_dir.is_dir():
                        config["model_config_list"].append({
                            "name": model_dir.name,
                            "base_path": str(model_dir),
                            "model_platform": "tensorflow"
                        })

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

    async def _reload_models(self):
        """Reloads all models in the serving server."""
        try:
            response = requests.post(f"{self.base_url}/v1/reloadconfig")
            if response.status_code == 200:
                logger.info("Models reloaded successfully")
            else:
                logger.warning(f"Failed to reload models: {response.status_code}")
        except Exception as e:
            logger.error(f"Error reloading models: {e}")

    async def predict(self, 
                     model_name: str, 
                     inputs: Dict[str, Any],
                     version: str = None) -> Dict[str, Any]:
        """
        Makes a prediction using the deployed model.
        
        Args:
            model_name: Name of the model
            inputs: Input data for prediction
            version: Model version (optional)
            
        Returns:
            Dict containing prediction results
        """
        try:
            # Prepare request URL
            url = f"{self.base_url}/v1/models/{model_name}"
            if version:
                url += f"/versions/{version}"
            url += ":predict"

            # Prepare request data
            request_data = {
                "instances": [inputs] if isinstance(inputs, dict) else inputs
            }

            # Make prediction request
            response = requests.post(url, json=request_data)
            response.raise_for_status()

            result = response.json()
            return result

        except Exception as e:
            logger.error(f"Prediction failed for model {model_name}: {e}")
            raise

    async def get_model_status(self, model_name: str = None) -> Dict[str, Any]:
        """
        Gets the status of deployed models.
        
        Args:
            model_name: Specific model name (optional)
            
        Returns:
            Dict containing model status information
        """
        try:
            if model_name:
                url = f"{self.base_url}/v1/models/{model_name}"
            else:
                url = f"{self.base_url}/v1/models"

            response = requests.get(url)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get model status: {e}")
            return {}

    async def get_model_metadata(self, model_name: str, version: str = None) -> Dict[str, Any]:
        """
        Gets metadata for a specific model.
        
        Args:
            model_name: Name of the model
            version: Model version (optional)
            
        Returns:
            Dict containing model metadata
        """
        try:
            url = f"{self.base_url}/v1/models/{model_name}"
            if version:
                url += f"/versions/{version}"
            url += "/metadata"

            response = requests.get(url)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get model metadata: {e}")
            return {}

    async def health_check(self) -> bool:
        """Checks if TensorFlow Serving is healthy."""
        try:
            response = requests.get(f"{self.base_url}/v1/models")
            return response.status_code == 200
        except:
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.create_task(self.stop_serving())
