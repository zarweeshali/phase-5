"""
Task routes for Phase V.

[Task]: T033-T035
[From]: specs/001-phase5-cloud/tasks.md §Phase 3
[Spec]: specs/001-phase5-cloud/spec.md §Functional Requirements

REST API endpoints for task CRUD operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.connection import get_db_session
from api.services.task_service import TaskService
from api.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskQueryParams,
)
from api.exceptions import TaskNotFoundError, TaskValidationError, HTTPError
from api.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# Dependency to get task service
async def get_task_service(
    session: AsyncSession = Depends(get_db_session),
) -> TaskService:
    """Get task service instance."""
    return TaskService(session)


# Mock user ID - in production, this would come from authentication
# For now, we use a placeholder that can be overridden via header
async def get_current_user(
    x_user_id: Optional[str] = Query(None, alias="x-user-id", description="User ID for testing"),
) -> str:
    """Get current user ID (mock for development)."""
    return x_user_id or "dev-user-123"


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    task_data: TaskCreate,
    user_id: str = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """
    Create a new task with title, description, due date, priority, and tags.
    
    **Required:**
    - `title`: Task title (1-200 characters)
    
    **Optional:**
    - `description`: Task description (up to 2000 characters)
    - `due_date`: When task is due (ISO 8601 format)
    - `priority`: high, medium, or low (default: medium)
    - `status`: pending, in_progress, completed, or cancelled (default: pending)
    - `tag_ids`: List of tag IDs to associate
    - `is_recurring`: Whether task repeats
    - `recurring_pattern_id`: ID of recurring pattern
    
    **Event Published:** `task-events` with event_type="created"
    """
    try:
        task = await service.create_task(task_data, user_id)
        logger.info("Task created: %s", task.id)
        return task
    except TaskValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict(),
        )


@router.get(
    "",
    response_model=List[TaskResponse],
    summary="List all tasks",
)
async def list_tasks(
    user_id: str = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
    q: Optional[str] = Query(None, description="Search in title and description"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> List[TaskResponse]:
    """
    List all tasks for the current user with optional filtering.
    
    **Query Parameters:**
    - `q`: Search keyword (searches title and description)
    - `priority`: Filter by priority (high, medium, low)
    - `status`: Filter by status (pending, in_progress, completed, cancelled)
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 20, max: 100)
    """
    # Build query params
    query_params = TaskQueryParams(
        q=q,
        priority=priority,
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    
    tasks = await service.list_tasks(user_id, query_params)
    logger.info("Listed %d tasks for user %s", len(tasks), user_id)
    
    return tasks


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a specific task",
)
async def get_task(
    task_id: int,
    user_id: str = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """
    Get a specific task by ID.
    
    **Path Parameters:**
    - `task_id`: Task ID
    
    **Returns:**
    - Task details including tags and recurring pattern
    """
    try:
        task = await service.get_task(task_id, user_id)
        logger.debug("Retrieved task: %s", task_id)
        return task
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Task not found", "task_id": task_id},
        )


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    user_id: str = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """
    Update an existing task.
    
    **Path Parameters:**
    - `task_id`: Task ID
    
    **Request Body:**
    - Any task field (title, description, due_date, priority, status, etc.)
    - `tag_ids`: Replace all tags with new list
    
    **Event Published:** `task-events` with event_type="updated"
    """
    try:
        task = await service.update_task(task_id, task_data, user_id)
        logger.info("Task updated: %s", task_id)
        return task
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Task not found", "task_id": task_id},
        )
    except TaskValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict(),
        )


@router.post(
    "/{task_id}/complete",
    response_model=TaskResponse,
    summary="Complete a task",
)
async def complete_task(
    task_id: int,
    user_id: str = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """
    Mark a task as completed.
    
    **Path Parameters:**
    - `task_id`: Task ID
    
    **Event Published:** `task-events` with event_type="completed"
    """
    try:
        task = await service.complete_task(task_id, user_id)
        logger.info("Task completed: %s", task_id)
        return task
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Task not found", "task_id": task_id},
        )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
async def delete_task(
    task_id: int,
    user_id: str = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> None:
    """
    Delete a task permanently.
    
    **Path Parameters:**
    - `task_id`: Task ID
    
    **Event Published:** `task-events` with event_type="deleted"
    """
    try:
        await service.delete_task(task_id, user_id)
        logger.info("Task deleted: %s", task_id)
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Task not found", "task_id": task_id},
        )
