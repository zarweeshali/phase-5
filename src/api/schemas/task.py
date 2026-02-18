"""
Task schemas for Phase V.

[Task]: T032
[From]: specs/001-phase5-cloud/tasks.md §Phase 3

Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from api.models.task import PriorityEnum, TaskStatusEnum, RecurringPatternEnum


# ============================================
# Recurring Pattern Schemas
# ============================================


class RecurringPatternBase(BaseModel):
    """Base schema for recurring pattern."""
    
    pattern_type: RecurringPatternEnum
    interval: int = Field(default=1, ge=1, description="Repeat interval (e.g., every 2 weeks)")
    end_date: Optional[datetime] = None
    custom_cron: Optional[str] = None


class RecurringPatternCreate(RecurringPatternBase):
    """Schema for creating a recurring pattern."""
    
    pass


class RecurringPatternResponse(RecurringPatternBase):
    """Schema for recurring pattern response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# ============================================
# Tag Schemas
# ============================================


class TagBase(BaseModel):
    """Base schema for tag."""
    
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#808080", pattern="^#[0-9A-Fa-f]{6}$")


class TagCreate(TagBase):
    """Schema for creating a tag."""
    
    pass


class TagResponse(TagBase):
    """Schema for tag response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# ============================================
# Task Schemas
# ============================================


class TaskBase(BaseModel):
    """Base schema for task."""
    
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    due_date: Optional[datetime] = None
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    status: TaskStatusEnum = Field(default=TaskStatusEnum.PENDING)
    is_recurring: bool = Field(default=False)
    recurring_pattern_id: Optional[int] = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    
    tag_ids: Optional[List[int]] = Field(default=None, description="List of tag IDs to associate")


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    due_date: Optional[datetime] = None
    priority: Optional[PriorityEnum] = None
    status: Optional[TaskStatusEnum] = None
    is_recurring: Optional[bool] = None
    recurring_pattern_id: Optional[int] = None
    tag_ids: Optional[List[int]] = Field(default=None, description="List of tag IDs to associate")


class TaskResponse(TaskBase):
    """Schema for task response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    tags: Optional[List[TagResponse]] = None
    recurring_pattern: Optional[RecurringPatternResponse] = None


class TaskListResponse(BaseModel):
    """Schema for paginated task list response."""
    
    items: List[TaskResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================
# Task Query Schemas (for search/filter/sort)
# ============================================


class TaskSortEnum(str, Enum):
    """Sort options for tasks."""
    
    DUE_DATE = "due_date"
    PRIORITY = "priority"
    CREATED_AT = "created_at"
    TITLE = "title"


class SortOrderEnum(str, Enum):
    """Sort order."""
    
    ASC = "asc"
    DESC = "desc"


class TaskQueryParams(BaseModel):
    """Query parameters for listing/filtering tasks."""
    
    # Search
    q: Optional[str] = Field(default=None, description="Search in title and description")
    
    # Filters
    priority: Optional[PriorityEnum] = None
    status: Optional[TaskStatusEnum] = None
    tag_id: Optional[int] = None
    is_recurring: Optional[bool] = None
    
    # Date range
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None
    
    # Sorting
    sort_by: TaskSortEnum = Field(default=TaskSortEnum.DUE_DATE)
    sort_order: SortOrderEnum = Field(default=SortOrderEnum.ASC)
    
    # Pagination
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
