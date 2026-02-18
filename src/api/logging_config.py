"""
Structured logging configuration for Phase V.

[Task]: T014
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Provides JSON structured logging with correlation ID, trace_id, span_id support.
Per Constitution Principle VI, all logs must be structured and include tracing context.
"""

import logging
import sys
from typing import Optional, Any, Dict
from datetime import datetime

from pythonjsonlogger import jsonlogger

from api.config import settings


class CorrelationIdFilter(logging.Filter):
    """
    Filter that adds correlation_id to log records.
    
    Correlation ID is used to track requests across services.
    Should be set at the beginning of each request.
    """
    
    def __init__(self, correlation_id: Optional[str] = None):
        """
        Initialize filter with optional correlation ID.
        
        Args:
            correlation_id: Correlation ID to add to logs
        """
        super().__init__()
        self.correlation_id = correlation_id
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation_id to log record."""
        record.correlation_id = self.correlation_id or "no-correlation-id"
        return True


class TraceIdFilter(logging.Filter):
    """
    Filter that adds trace_id and span_id to log records.
    
    Used for distributed tracing with OpenTelemetry.
    """
    
    def __init__(self):
        super().__init__()
        self.trace_id: Optional[str] = None
        self.span_id: Optional[str] = None
    
    def set_trace_context(self, trace_id: str, span_id: str) -> None:
        """Set trace context for current request."""
        self.trace_id = trace_id
        self.span_id = span_id
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add trace_id and span_id to log record."""
        record.trace_id = self.trace_id or "no-trace-id"
        record.span_id = self.span_id or "no-span-id"
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter with additional fields.
    
    Adds timestamp, level, logger name, and custom fields.
    """
    
    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """
        Add custom fields to log record.
        
        Args:
            log_record: Log record dictionary to populate
            record: Python logging LogRecord
            message_dict: Message dictionary
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Add log level
        log_record["level"] = record.levelname
        
        # Add logger name
        log_record["logger"] = record.name
        
        # Add correlation ID if present
        log_record["correlation_id"] = getattr(record, "correlation_id", None)
        
        # Add trace context if present
        log_record["trace_id"] = getattr(record, "trace_id", None)
        log_record["span_id"] = getattr(record, "span_id", None)
        
        # Add filename and line number in debug mode
        if settings.log_level == "DEBUG":
            log_record["file"] = record.filename
            log_record["line"] = record.lineno


def setup_logging(
    log_level: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> logging.Logger:
    """
    Setup structured JSON logging.
    
    Args:
        log_level: Log level (default: from settings)
        correlation_id: Optional correlation ID for request tracking
        
    Returns:
        Root logger configured with JSON formatter
        
    Usage:
        logger = setup_logging()
        logger.info("Application started")
    """
    level = log_level or settings.log_level
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = CustomJsonFormatter(
        fmt="%(timestamp)s %(level)s %(logger)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    
    # Add filters
    correlation_filter = CorrelationIdFilter(correlation_id)
    trace_filter = TraceIdFilter()
    
    console_handler.addFilter(correlation_filter)
    console_handler.addFilter(trace_filter)
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Log setup information
    root_logger.info(
        "Logging initialized",
        extra={
            "log_level": level,
            "app_name": settings.app_name,
            "app_env": settings.app_env,
        },
    )
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
        
    Usage:
        logger = get_logger(__name__)
        logger.info("Module initialized")
    """
    return logging.getLogger(name)


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID for current request.
    
    Args:
        correlation_id: Unique correlation ID
        
    Usage:
        set_correlation_id("req-123-abc")
        logger.info("Processing request")
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        for filter_ in handler.filters:
            if isinstance(filter_, CorrelationIdFilter):
                filter_.correlation_id = correlation_id


def set_trace_context(trace_id: str, span_id: str) -> None:
    """
    Set trace context for distributed tracing.
    
    Args:
        trace_id: Trace ID from OpenTelemetry
        span_id: Span ID from OpenTelemetry
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        for filter_ in handler.filters:
            if isinstance(filter_, TraceIdFilter):
                filter_.set_trace_context(trace_id, span_id)


# Global logger instance
logger = get_logger(__name__)
