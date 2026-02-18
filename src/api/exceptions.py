"""
Custom exceptions for Phase V.

[Task]: T013
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Provides custom exception classes for error handling.
"""

from typing import Any, Optional, Dict


class PhaseVError(Exception):
    """Base exception for Phase V application."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


# ============================================
# Task Errors
# ============================================


class TaskNotFoundError(PhaseVError):
    """Raised when a task is not found."""
    
    def __init__(self, task_id: int, details: Optional[Dict[str, Any]] = None):
        message = f"Task not found: {task_id}"
        super().__init__(message, {"task_id": task_id, **(details or {})})


class TaskValidationError(PhaseVError):
    """Raised when task validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(message, details)


class TaskPermissionError(PhaseVError):
    """Raised when user doesn't have permission to access a task."""
    
    def __init__(self, task_id: int, user_id: str):
        message = f"User {user_id} does not have permission to access task {task_id}"
        super().__init__(message, {"task_id": task_id, "user_id": user_id})


# ============================================
# Reminder Errors
# ============================================


class ReminderError(PhaseVError):
    """Base exception for reminder-related errors."""
    
    pass


class ReminderNotFoundError(PhaseVError):
    """Raised when a reminder is not found."""
    
    def __init__(self, reminder_id: int):
        message = f"Reminder not found: {reminder_id}"
        super().__init__(message, {"reminder_id": reminder_id})


class ReminderSchedulingError(PhaseVError):
    """Raised when reminder scheduling fails."""
    
    def __init__(self, task_id: int, reason: str):
        message = f"Failed to schedule reminder for task {task_id}: {reason}"
        super().__init__(message, {"task_id": task_id, "reason": reason})


# ============================================
# Kafka / Dapr Errors
# ============================================


class KafkaPublishError(PhaseVError):
    """Raised when publishing to Kafka fails."""
    
    def __init__(self, topic: str, event_type: str, reason: str):
        message = f"Failed to publish {event_type} to {topic}: {reason}"
        super().__init__(
            message,
            {"topic": topic, "event_type": event_type, "reason": reason},
        )


class DaprCommunicationError(PhaseVError):
    """Raised when Dapr sidecar communication fails."""
    
    def __init__(self, operation: str, reason: str):
        message = f"Dapr {operation} failed: {reason}"
        super().__init__(message, {"operation": operation, "reason": reason})


# ============================================
# Database Errors
# ============================================


class DatabaseError(PhaseVError):
    """Raised when database operation fails."""
    
    def __init__(self, operation: str, reason: str):
        message = f"Database {operation} failed: {reason}"
        super().__init__(message, {"operation": operation, "reason": reason})


class DatabaseConnectionError(PhaseVError):
    """Raised when database connection fails."""
    
    def __init__(self, reason: str):
        message = f"Database connection failed: {reason}"
        super().__init__(message, {"reason": reason})


# ============================================
# Validation Errors
# ============================================


class ValidationError(PhaseVError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        details = {"field": field}
        if value is not None:
            details["value"] = str(value)[:100]  # Truncate long values
        super().__init__(message, details)


# ============================================
# Authentication / Authorization Errors
# ============================================


class AuthenticationError(PhaseVError):
    """Raised when authentication fails."""
    
    def __init__(self, reason: str = "Authentication failed"):
        super().__init__(reason, {"reason": reason})


class AuthorizationError(PhaseVError):
    """Raised when user is not authorized for an action."""
    
    def __init__(self, action: str, resource: str):
        message = f"Not authorized to {action} on {resource}"
        super().__init__(message, {"action": action, "resource": resource})


# ============================================
# HTTP Error Responses
# ============================================


class HTTPError(PhaseVError):
    """Base HTTP error with status code."""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        super().__init__(message, details)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "status_code": self.status_code,
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class BadRequestError(HTTPError):
    """HTTP 400 Bad Request."""
    
    def __init__(self, message: str = "Bad request", details: Optional[Dict[str, Any]] = None):
        super().__init__(400, message, details)


class UnauthorizedError(HTTPError):
    """HTTP 401 Unauthorized."""
    
    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(401, message, details)


class ForbiddenError(HTTPError):
    """HTTP 403 Forbidden."""
    
    def __init__(self, message: str = "Forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(403, message, details)


class NotFoundError(HTTPError):
    """HTTP 404 Not Found."""
    
    def __init__(self, message: str = "Not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(404, message, details)


class ConflictError(HTTPError):
    """HTTP 409 Conflict."""
    
    def __init__(self, message: str = "Conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(409, message, details)


class InternalServerError(HTTPError):
    """HTTP 500 Internal Server Error."""
    
    def __init__(
        self, message: str = "Internal server error", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(500, message, details)
