"""Storage and search API endpoints for SOC Agent."""

from __future__ import annotations

import hashlib
import mimetypes
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import get_current_user
from .config import SETTINGS
from .database import ElasticsearchIndex, StorageFile, TimeSeriesMetric, get_db
from .elasticsearch_service import elasticsearch_service, search_logs
from .storage import storage_service
from .timeseries_service import get_dashboard_metrics, timeseries_service

# API router
router = APIRouter(prefix="/api/v1/storage", tags=["storage"])


# Pydantic models for request/response
class FileUploadResponse(BaseModel):
    id: int
    object_key: str
    filename: str
    folder: str
    size: int
    content_type: str
    public_url: str
    file_hash: str
    created_at: datetime


class FileListResponse(BaseModel):
    files: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int


class SearchRequest(BaseModel):
    query: str = ""
    index_name: str = "audit_logs"
    filters: Optional[Dict[str, Any]] = None
    date_range: Optional[Dict[str, str]] = None
    size: int = 100
    from_: int = 0
    sort: Optional[List[Dict[str, str]]] = None


class SearchResponse(BaseModel):
    hits: List[Dict[str, Any]]
    total: int
    took: int
    aggregations: Optional[Dict[str, Any]] = None


class MetricsResponse(BaseModel):
    performance: Dict[str, Any]
    api: Dict[str, Any]
    alerts: Dict[str, Any]
    system: Dict[str, Any]


# Storage endpoints
@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    folder: str = Form("uploads"),
    is_public: bool = Form(False),
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file to storage."""
    if not SETTINGS.storage_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Storage is not enabled"
        )
    
    try:
        # Read file data
        file_data = await file.read()
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Check if file already exists
        existing_file = db.query(StorageFile).filter(
            StorageFile.file_hash == file_hash,
            StorageFile.uploaded_by == current_user.id
        ).first()
        
        if existing_file:
            return FileUploadResponse(
                id=existing_file.id,
                object_key=existing_file.object_key,
                filename=existing_file.filename,
                folder=existing_file.folder,
                size=existing_file.size,
                content_type=existing_file.content_type,
                public_url=existing_file.public_url,
                file_hash=existing_file.file_hash,
                created_at=existing_file.created_at
            )
        
        # Upload to storage
        file_info = storage_service.upload_file(
            file_data=file_data,
            filename=file.filename,
            folder=folder,
            metadata={
                'uploaded_by': str(current_user.id),
                'is_public': str(is_public)
            }
        )
        
        # Save to database
        storage_file = StorageFile(
            object_key=file_info['object_key'],
            filename=file.filename,
            folder=folder,
            size=file_info['size'],
            content_type=file_info['content_type'],
            storage_provider=SETTINGS.storage_provider,
            bucket_name=SETTINGS.storage_bucket_name,
            public_url=file_info['url'],
            file_hash=file_hash,
            metadata=file_info['metadata'],
            is_public=is_public,
            uploaded_by=current_user.id
        )
        
        db.add(storage_file)
        db.commit()
        db.refresh(storage_file)
        
        return FileUploadResponse(
            id=storage_file.id,
            object_key=storage_file.object_key,
            filename=storage_file.filename,
            folder=storage_file.folder,
            size=storage_file.size,
            content_type=storage_file.content_type,
            public_url=storage_file.public_url,
            file_hash=storage_file.file_hash,
            created_at=storage_file.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/files", response_model=FileListResponse)
async def list_files(
    folder: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List uploaded files."""
    try:
        # Build query
        query = db.query(StorageFile).filter(StorageFile.uploaded_by == current_user.id)
        
        if folder:
            query = query.filter(StorageFile.folder == folder)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        files = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return FileListResponse(
            files=[file.to_dict() for file in files],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )


@router.get("/files/{file_id}")
async def get_file(
    file_id: int,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file information."""
    try:
        file = db.query(StorageFile).filter(
            StorageFile.id == file_id,
            StorageFile.uploaded_by == current_user.id
        ).first()
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return file.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file: {str(e)}"
        )


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a file."""
    try:
        file = db.query(StorageFile).filter(
            StorageFile.id == file_id,
            StorageFile.uploaded_by == current_user.id
        ).first()
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Download file data
        file_data = storage_service.download_file(file.object_key)
        
        # Update access count
        file.access_count += 1
        file.last_accessed = datetime.utcnow()
        db.commit()
        
        # Return file as streaming response
        return StreamingResponse(
            iter([file_data]),
            media_type=file.content_type,
            headers={
                "Content-Disposition": f"attachment; filename={file.filename}",
                "Content-Length": str(file.size)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a file."""
    try:
        file = db.query(StorageFile).filter(
            StorageFile.id == file_id,
            StorageFile.uploaded_by == current_user.id
        ).first()
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Delete from storage
        storage_service.delete_file(file.object_key)
        
        # Delete from database
        db.delete(file)
        db.commit()
        
        return {"message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get("/stats")
async def get_storage_stats(
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get storage statistics."""
    try:
        # Get user's file stats
        user_files = db.query(StorageFile).filter(StorageFile.uploaded_by == current_user.id)
        
        total_files = user_files.count()
        total_size = sum(file.size for file in user_files.all())
        
        # Get storage service stats
        storage_stats = storage_service.get_storage_stats()
        
        return {
            "user_files": {
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            },
            "storage_service": storage_stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage stats: {str(e)}"
        )


# Search endpoints
@router.post("/search", response_model=SearchResponse)
async def search_logs(
    search_request: SearchRequest,
    current_user: Any = Depends(get_current_user)
):
    """Search logs in Elasticsearch."""
    if not SETTINGS.elasticsearch_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Elasticsearch is not enabled"
        )
    
    try:
        # Create search query
        query = elasticsearch_service.create_search_query(
            search_term=search_request.query,
            filters=search_request.filters,
            date_range=search_request.date_range,
            sort=search_request.sort
        )
        
        # Search logs
        response = search_logs(
            search_request.index_name,
            query,
            search_request.size,
            search_request.from_
        )
        
        # Process response
        hits = []
        for hit in response.get('hits', {}).get('hits', []):
            hits.append({
                'id': hit['_id'],
                'source': hit['_source'],
                'score': hit.get('_score', 0)
            })
        
        return SearchResponse(
            hits=hits,
            total=response.get('hits', {}).get('total', {}).get('value', 0),
            took=response.get('took', 0),
            aggregations=response.get('aggregations')
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search logs: {str(e)}"
        )


@router.get("/search/indices")
async def list_elasticsearch_indices(
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List Elasticsearch indices."""
    if not SETTINGS.elasticsearch_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Elasticsearch is not enabled"
        )
    
    try:
        indices = db.query(ElasticsearchIndex).filter(ElasticsearchIndex.is_active == True).all()
        return [index.to_dict() for index in indices]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list indices: {str(e)}"
        )


@router.get("/search/health")
async def get_elasticsearch_health(
    current_user: Any = Depends(get_current_user)
):
    """Get Elasticsearch cluster health."""
    if not SETTINGS.elasticsearch_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Elasticsearch is not enabled"
        )
    
    try:
        health = elasticsearch_service.get_cluster_health()
        return health
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Elasticsearch health: {str(e)}"
        )


# Metrics endpoints
@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    time_range: str = Query("24h"),
    current_user: Any = Depends(get_current_user)
):
    """Get time-series metrics."""
    if not SETTINGS.timeseries_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time-series database is not enabled"
        )
    
    try:
        metrics = get_dashboard_metrics(time_range)
        return MetricsResponse(**metrics)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/metrics/health")
async def get_timeseries_health(
    current_user: Any = Depends(get_current_user)
):
    """Get time-series database health."""
    if not SETTINGS.timeseries_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time-series database is not enabled"
        )
    
    try:
        health = timeseries_service.get_health_status()
        return health
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get time-series health: {str(e)}"
        )


@router.get("/metrics/summary")
async def get_metrics_summary(
    measurement: str = Query("performance_metrics"),
    time_range: str = Query("1h"),
    current_user: Any = Depends(get_current_user)
):
    """Get metrics summary for a measurement."""
    if not SETTINGS.timeseries_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time-series database is not enabled"
        )
    
    try:
        summary = timeseries_service.get_metrics_summary(measurement, time_range)
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics summary: {str(e)}"
        )


@router.get("/metrics/timeseries")
async def get_timeseries_data(
    measurement: str = Query("performance_metrics"),
    field: str = Query("value"),
    time_range: str = Query("1h"),
    tags: Optional[str] = Query(None),
    current_user: Any = Depends(get_current_user)
):
    """Get time series data for a specific measurement and field."""
    if not SETTINGS.timeseries_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time-series database is not enabled"
        )
    
    try:
        # Parse tags if provided
        tag_dict = {}
        if tags:
            for tag_pair in tags.split(','):
                if '=' in tag_pair:
                    key, value = tag_pair.split('=', 1)
                    tag_dict[key.strip()] = value.strip()
        
        data = timeseries_service.get_time_series_data(
            measurement, field, time_range, tag_dict
        )
        
        return data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get time series data: {str(e)}"
        )
