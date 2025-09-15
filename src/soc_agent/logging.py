from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict

from .config import SETTINGS


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add module and function info
        if record.module:
            payload["module"] = record.module
        if record.funcName:
            payload["function"] = record.funcName
        if record.lineno:
            payload["line"] = record.lineno
            
        # Add exception info
        if record.exc_info:
            payload["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "getMessage"
            }:
                payload[key] = value
                
        return json.dumps(payload, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_json_logging(level: int = None) -> None:
    """Setup logging with appropriate formatter and level."""
    if level is None:
        level = getattr(logging, SETTINGS.log_level.upper(), logging.INFO)
    
    # Clear existing handlers
    root = logging.getLogger()
    root.handlers.clear()
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter based on configuration
    if SETTINGS.log_format.lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter())
    
    # Configure root logger
    root.setLevel(level)
    root.addHandler(handler)
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
