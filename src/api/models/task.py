"""
Task models for Phase V.

[Task]: T022-T026
[From]: specs/001-phase5-cloud/tasks.md §Phase 3
[Spec]: specs/001-phase5-cloud/spec.md §Key Entities
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, JSON, ForeignKey, func

from api.models.base import BaseModel


# ============================================
# Enums
# ============================================


class PriorityEnum(str, Enum):
    """Task priority levels."""
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatusEnum(str, Enum):
    """Task status values."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RecurringPatternEnum(str, Enum):
    """Recurring pattern types."""
    
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


# ============================================
# Models
# ============================================


class Tag(BaseModel, table=True):
    """
    Tag model for categorizing tasks.
    
    [Task]: T026
    """
    
    __tablename__ = "tags"
    
    name: str = Field(..., max_length=50, index=True)
    color: Optional[str] = Field(default="#808080", max_length=7)  # Hex color code
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )
    
    # Relationships
    tasks: list["TaskTag"] = Relationship(back_populates="tag")


class Task(BaseModel, table=True):
    """
    Task model - core entity for todo app.
    
    [Task]: T022
    [Spec]: specs/001-phase5-cloud/spec.md §Key Entities - Task
    """
    
    __tablename__ = "tasks"
    
    # Core fields
    title: str = Field(..., max_length=200, index=True)
    description: Optional[str] = Field(default=None, max_length=2000)
    
    # Due date and timing
    due_date: Optional[datetime] = Field(default=None, index=True)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )
    
    # Priority and status
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM, sa_column=Column(SQLEnum(PriorityEnum), index=True))
    status: TaskStatusEnum = Field(default=TaskStatusEnum.PENDING, sa_column=Column(SQLEnum(TaskStatusEnum), index=True))
    
    # Recurring task fields
    is_recurring: bool = Field(default=False)
    recurring_pattern_id: Optional[int] = Field(default=None, foreign_key="recurringpatterns.id")
    
    # Relationships
    tags: list["TaskTag"] = Relationship(back_populates="task")
    recurring_pattern: Optional["RecurringPattern"] = Relationship(back_populates="tasks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Submit quarterly report",
                "description": "Complete and submit Q1 financial report",
                "due_date": "2026-03-31T17:00:00Z",
                "priority": "high",
                "status": "pending",
                "is_recurring": False,
                "user_id": "user-123",
            }
        }


class RecurringPattern(BaseModel, table=True):
    """
    Recurring pattern model for repeating tasks.
    
    [Task]: T025
    [Spec]: specs/001-phase5-cloud/spec.md §Key Entities - RecurringPattern
    """
    
    __tablename__ = "recurringpatterns"
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )
    
    pattern_type: RecurringPatternEnum = Field(..., sa_column=Column(SQLEnum(RecurringPatternEnum)))
    interval: int = Field(default=1, ge=1)  # e.g., every 2 weeks
    end_date: Optional[datetime] = Field(default=None)
    custom_cron: Optional[str] = Field(default=None)  # For custom patterns
    
    # Relationships
    tasks: list["Task"] = Relationship(back_populates="recurring_pattern")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pattern_type": "weekly",
                "interval": 1,
                "end_date": None,
                "custom_cron": None,
            }
        }


class TaskTag(BaseModel, table=True):
    """
    Association table for many-to-many relationship between tasks and tags.
    
    [Task]: T026 (supporting)
    """
    
    __tablename__ = "tasktags"
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )
    
    task_id: int = Field(..., foreign_key="tasks.id", primary_key=True)
    tag_id: int = Field(..., foreign_key="tags.id", primary_key=True)
    
    # Relationships
    task: Optional["Task"] = Relationship(back_populates="tags")
    tag: Optional["Tag"] = Relationship(back_populates="tasks")
