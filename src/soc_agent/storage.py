"""S3-compatible storage service for SOC Agent."""

from __future__ import annotations

import hashlib
import mimetypes
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from sqlalchemy.orm import Session

from .config import SETTINGS
from .database import get_db

# Storage providers configuration
STORAGE_PROVIDERS = {
    "s3": {
        "service_name": "s3",
        "endpoint_url": None,
        "region_name": "us-east-1"
    },
    "minio": {
        "service_name": "s3",
        "endpoint_url": "http://localhost:9000",
        "region_name": "us-east-1"
    },
    "gcs": {
        "service_name": "s3",
        "endpoint_url": "https://storage.googleapis.com",
        "region_name": "us-east-1"
    },
    "azure": {
        "service_name": "s3",
        "endpoint_url": "https://{account}.blob.core.windows.net",
        "region_name": "us-east-1"
    }
}


class StorageError(Exception):
    """Storage related errors."""
    pass


class StorageService:
    """S3-compatible storage service."""
    
    def __init__(self):
        self.config = self._get_storage_config()
        self.client = None
        self.bucket_name = SETTINGS.storage_bucket_name
        self.public_url = SETTINGS.storage_public_url
        
        if SETTINGS.storage_enabled:
            self._initialize_client()
    
    def _get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration based on provider."""
        provider = SETTINGS.storage_provider.lower()
        if provider not in STORAGE_PROVIDERS:
            raise StorageError(f"Unsupported storage provider: {provider}")
        
        config = STORAGE_PROVIDERS[provider].copy()
        
        # Override with custom endpoint if provided
        if SETTINGS.storage_endpoint_url:
            config["endpoint_url"] = SETTINGS.storage_endpoint_url
        
        # Override region if provided
        if SETTINGS.storage_region:
            config["region_name"] = SETTINGS.storage_region
        
        return config
    
    def _initialize_client(self):
        """Initialize S3 client."""
        try:
            self.client = boto3.client(
                service_name=self.config["service_name"],
                endpoint_url=self.config["endpoint_url"],
                region_name=self.config["region_name"],
                aws_access_key_id=SETTINGS.storage_access_key,
                aws_secret_access_key=SETTINGS.storage_secret_key,
                use_ssl=SETTINGS.storage_use_ssl,
                verify=SETTINGS.storage_use_ssl
            )
            
            # Test connection and create bucket if needed
            self._ensure_bucket_exists()
            
        except NoCredentialsError:
            raise StorageError("Storage credentials not configured")
        except Exception as e:
            raise StorageError(f"Failed to initialize storage client: {str(e)}")
    
    def _ensure_bucket_exists(self):
        """Ensure the storage bucket exists."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    self.client.create_bucket(Bucket=self.bucket_name)
                except ClientError as create_error:
                    raise StorageError(f"Failed to create bucket: {str(create_error)}")
            else:
                raise StorageError(f"Failed to access bucket: {str(e)}")
    
    def _generate_object_key(self, filename: str, folder: str = "uploads") -> str:
        """Generate unique object key for storage."""
        # Generate unique identifier
        unique_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        
        # Get file extension
        _, ext = os.path.splitext(filename)
        
        # Create object key
        object_key = f"{folder}/{timestamp}/{unique_id}{ext}"
        
        return object_key
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type for file."""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    def upload_file(self, file_data: bytes, filename: str, folder: str = "uploads", 
                   metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Upload file to storage."""
        if not self.client:
            raise StorageError("Storage not initialized")
        
        try:
            # Generate object key
            object_key = self._generate_object_key(filename, folder)
            
            # Prepare metadata
            upload_metadata = {
                'original_filename': filename,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'content_type': self._get_content_type(filename),
                'file_size': str(len(file_data))
            }
            
            if metadata:
                upload_metadata.update(metadata)
            
            # Upload file
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_data,
                ContentType=self._get_content_type(filename),
                Metadata=upload_metadata
            )
            
            # Generate file info
            file_info = {
                'object_key': object_key,
                'filename': filename,
                'folder': folder,
                'size': len(file_data),
                'content_type': self._get_content_type(filename),
                'url': self.get_public_url(object_key),
                'metadata': upload_metadata
            }
            
            return file_info
            
        except ClientError as e:
            raise StorageError(f"Failed to upload file: {str(e)}")
    
    def download_file(self, object_key: str) -> bytes:
        """Download file from storage."""
        if not self.client:
            raise StorageError("Storage not initialized")
        
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return response['Body'].read()
        except ClientError as e:
            raise StorageError(f"Failed to download file: {str(e)}")
    
    def delete_file(self, object_key: str) -> bool:
        """Delete file from storage."""
        if not self.client:
            raise StorageError("Storage not initialized")
        
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except ClientError as e:
            raise StorageError(f"Failed to delete file: {str(e)}")
    
    def get_file_info(self, object_key: str) -> Dict[str, Any]:
        """Get file information from storage."""
        if not self.client:
            raise StorageError("Storage not initialized")
        
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return {
                'object_key': object_key,
                'size': response['ContentLength'],
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'],
                'metadata': response.get('Metadata', {}),
                'url': self.get_public_url(object_key)
            }
        except ClientError as e:
            raise StorageError(f"Failed to get file info: {str(e)}")
    
    def list_files(self, folder: str = "", prefix: str = "", 
                  max_keys: int = 1000) -> List[Dict[str, Any]]:
        """List files in storage."""
        if not self.client:
            raise StorageError("Storage not initialized")
        
        try:
            # Build prefix
            search_prefix = f"{folder}/" if folder else ""
            if prefix:
                search_prefix += prefix
            
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=search_prefix,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'object_key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'url': self.get_public_url(obj['Key'])
                })
            
            return files
        except ClientError as e:
            raise StorageError(f"Failed to list files: {str(e)}")
    
    def get_public_url(self, object_key: str) -> str:
        """Get public URL for file."""
        if self.public_url:
            return urljoin(self.public_url, object_key)
        
        # Generate presigned URL
        if not self.client:
            raise StorageError("Storage not initialized")
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=3600  # 1 hour
            )
            return url
        except ClientError as e:
            raise StorageError(f"Failed to generate URL: {str(e)}")
    
    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for file access."""
        if not self.client:
            raise StorageError("Storage not initialized")
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise StorageError(f"Failed to generate presigned URL: {str(e)}")
    
    def copy_file(self, source_key: str, dest_key: str) -> bool:
        """Copy file within storage."""
        if not self.client:
            raise StorageError("Storage not initialized")
        
        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            self.client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key
            )
            return True
        except ClientError as e:
            raise StorageError(f"Failed to copy file: {str(e)}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        if not self.client:
            raise StorageError("Storage not initialized")
        
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name)
            
            total_size = sum(obj['Size'] for obj in response.get('Contents', []))
            file_count = len(response.get('Contents', []))
            
            return {
                'total_files': file_count,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'bucket_name': self.bucket_name,
                'provider': SETTINGS.storage_provider
            }
        except ClientError as e:
            raise StorageError(f"Failed to get storage stats: {str(e)}")
    
    def cleanup_old_files(self, days: int = 30) -> int:
        """Clean up files older than specified days."""
        if not self.client:
            raise StorageError("Storage not initialized")
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            response = self.client.list_objects_v2(Bucket=self.bucket_name)
            
            deleted_count = 0
            for obj in response.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    self.client.delete_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    deleted_count += 1
            
            return deleted_count
        except ClientError as e:
            raise StorageError(f"Failed to cleanup old files: {str(e)}")


# Global storage service instance
storage_service = StorageService()


class FileMetadata:
    """File metadata model for database storage."""
    
    def __init__(self, object_key: str, filename: str, folder: str, 
                 size: int, content_type: str, metadata: Dict[str, Any]):
        self.object_key = object_key
        self.filename = filename
        self.folder = folder
        self.size = size
        self.content_type = content_type
        self.metadata = metadata
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'object_key': self.object_key,
            'filename': self.filename,
            'folder': self.folder,
            'size': self.size,
            'content_type': self.content_type,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


def upload_file_to_storage(file_data: bytes, filename: str, folder: str = "uploads",
                          metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Upload file to storage and return file info."""
    return storage_service.upload_file(file_data, filename, folder, metadata)


def download_file_from_storage(object_key: str) -> bytes:
    """Download file from storage."""
    return storage_service.download_file(object_key)


def delete_file_from_storage(object_key: str) -> bool:
    """Delete file from storage."""
    return storage_service.delete_file(object_key)


def get_file_url(object_key: str) -> str:
    """Get public URL for file."""
    return storage_service.get_public_url(object_key)
