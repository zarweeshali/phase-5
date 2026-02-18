"""
Base model class for Phase V.

[Task]: T007
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Provides common fields (id, created_at, updated_at, user_id) for all models.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, func


class BaseModel(SQLModel):
    """
    Base model with common fields for table models.
    
    All domain models should inherit from this class to ensure
    consistent fields across the application.
    """
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(..., index=True, nullable=False)


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.
    
    Adds deleted_at field to support soft deletes per Constitution Principle IX.
    """
    
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None
    
    def mark_deleted(self) -> None:
        """Mark record as deleted."""
        self.deleted_at = datetime.utcnow()
