"""Request/response compression middleware."""

from __future__ import annotations

import gzip
import brotli
import logging
from typing import Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class CompressionMiddleware(BaseHTTPMiddleware):
    """Compression middleware for request/response optimization."""
    
    def __init__(self, app, minimum_size: int = 1000, compressible_types: Optional[list] = None):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compressible_types = compressible_types or [
            "application/json",
            "application/xml",
            "text/html",
            "text/css",
            "text/javascript",
            "text/plain",
            "application/javascript",
            "application/x-javascript",
            "text/xml",
            "application/xml+rss",
            "application/atom+xml",
            "image/svg+xml"
        ]
    
    def _should_compress(self, response: Response) -> bool:
        """Determine if response should be compressed."""
        # Check content type
        content_type = response.headers.get("content-type", "").split(";")[0]
        if content_type not in self.compressible_types:
            return False
        
        # Check content length
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.minimum_size:
            return False
        
        # Check if already compressed
        if response.headers.get("content-encoding"):
            return False
        
        return True
    
    def _get_compression_type(self, request: Request) -> str:
        """Get preferred compression type based on client support."""
        accept_encoding = request.headers.get("accept-encoding", "").lower()
        
        # Prefer Brotli for better compression
        if "br" in accept_encoding:
            return "br"
        elif "gzip" in accept_encoding:
            return "gzip"
        else:
            return "none"
    
    def _compress_content(self, content: bytes, compression_type: str) -> bytes:
        """Compress content using specified compression type."""
        if compression_type == "gzip":
            return gzip.compress(content, compresslevel=6)
        elif compression_type == "br":
            return brotli.compress(content, quality=4)
        else:
            return content
    
    async def dispatch(self, request: Request, call_next):
        """Process request with compression."""
        # Process request
        response = await call_next(request)
        
        # Check if response should be compressed
        if not self._should_compress(response):
            return response
        
        # Get compression type
        compression_type = self._get_compression_type(request)
        if compression_type == "none":
            return response
        
        # Get response body
        if hasattr(response, 'body'):
            body = response.body
        elif hasattr(response, 'content'):
            body = response.content
        else:
            # For streaming responses, we can't compress easily
            return response
        
        if not body:
            return response
        
        # Compress content
        try:
            compressed_body = self._compress_content(body, compression_type)
            
            # Update response
            response.headers["content-encoding"] = compression_type
            response.headers["content-length"] = str(len(compressed_body))
            response.headers["vary"] = "Accept-Encoding"
            
            # Update body
            if hasattr(response, 'body'):
                response.body = compressed_body
            elif hasattr(response, 'content'):
                response.content = compressed_body
            
            logger.debug(f"Compressed response: {len(body)} -> {len(compressed_body)} bytes ({compression_type})")
            
        except Exception as e:
            logger.error(f"Compression error: {e}")
            # Return original response on compression error
        
        return response

def get_compression_stats() -> Dict[str, Any]:
    """Get compression statistics."""
    return {
        "supported_types": ["gzip", "brotli"],
        "minimum_size": 1000,
        "compressible_types": [
            "application/json",
            "application/xml", 
            "text/html",
            "text/css",
            "text/javascript",
            "text/plain"
        ]
    }
