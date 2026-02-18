"""
Task service for Phase V.

[Task]: T027-T031
[From]: specs/001-phase5-cloud/tasks.md §Phase 3
[Spec]: specs/001-phase5-cloud/spec.md §Functional Requirements

Business logic for task CRUD operations with event publishing.
Per Constitution Principle I, all operations publish events via Dapr.
"""

from datetime import datetime
from typing import Optional, List
import logging

from sqlmodel import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.task import Task, Tag, TaskTag, RecurringPattern, PriorityEnum, TaskStatusEnum
from api.schemas.task import TaskCreate, TaskUpdate, TaskQueryParams
from api.dapr.publisher import publish_task_event, publish_task_update_event
from api.exceptions import TaskNotFoundError, TaskValidationError
from api.logging_config import get_logger

logger = get_logger(__name__)


class TaskService:
    """
    Service for task business logic.
    
    All operations publish events via Dapr Pub/Sub per Constitution Principle I.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize task service.
        
        Args:
            db_session: Async database session
        """
        self.db = db_session
    
    async def create_task(
        self,
        task_data: TaskCreate,
        user_id: str,
    ) -> Task:
        """
        Create a new task.
        
        [Task]: T027
        [Spec]: FR-001, FR-007
        
        Args:
            task_data: Task creation data
            user_id: User creating the task
            
        Returns:
            Task: Created task
            
        Raises:
            TaskValidationError: If validation fails
        """
        logger.info("Creating task for user %s", user_id, extra={"user_id": user_id})
        
        # Validate due date if provided
        if task_data.due_date and task_data.due_date < datetime.utcnow():
            raise TaskValidationError(
                "Due date cannot be in the past",
                field="due_date",
            )
        
        # Create task
        task = Task(
            title=task_data.title,
            description=task_data.description,
            due_date=task_data.due_date,
            priority=task_data.priority,
            status=task_data.status,
            is_recurring=task_data.is_recurring,
            recurring_pattern_id=task_data.recurring_pattern_id,
            user_id=user_id,
        )
        
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        
        # Associate tags if provided
        if task_data.tag_ids:
            await self._associate_tags(task, task_data.tag_ids)
        
        await self.db.commit()
        await self.db.refresh(task)
        
        # Publish event via Dapr (Constitution Principle I)
        await publish_task_event(
            event_type="created",
            task_data=self._task_to_dict(task),
            user_id=user_id,
        )
        
        logger.info(
            "Task created successfully: %s",
            task.id,
            extra={"task_id": task.id, "user_id": user_id},
        )
        
        return task
    
    async def get_task(self, task_id: int, user_id: str) -> Task:
        """
        Get task by ID.
        
        [Task]: T027
        [Spec]: FR-001
        
        Args:
            task_id: Task ID
            user_id: User ID (for authorization)
            
        Returns:
            Task: Retrieved task
            
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        logger.debug("Getting task %s for user %s", task_id, user_id)
        
        statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await self.db.execute(statement)
        task = result.scalar_one_or_none()
        
        if not task:
            raise TaskNotFoundError(task_id)
        
        return task
    
    async def update_task(
        self,
        task_id: int,
        task_data: TaskUpdate,
        user_id: str,
    ) -> Task:
        """
        Update an existing task.
        
        [Task]: T028
        [Spec]: FR-001, FR-008
        
        Args:
            task_id: Task ID
            task_data: Update data
            user_id: User ID
            
        Returns:
            Task: Updated task
            
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        logger.info("Updating task %s for user %s", task_id, user_id)
        
        task = await self.get_task(task_id, user_id)
        
        # Update fields
        update_data = task_data.model_dump(exclude_unset=True, exclude={"tag_ids"})
        for field, value in update_data.items():
            if value is not None:
                setattr(task, field, value)
        
        # Update tags if provided
        if task_data.tag_ids is not None:
            await self._update_tags(task, task_data.tag_ids)
        
        task.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(task)
        
        # Publish event via Dapr
        await publish_task_event(
            event_type="updated",
            task_data=self._task_to_dict(task),
            user_id=user_id,
        )
        
        logger.info("Task updated successfully: %s", task_id)
        
        return task
    
    async def complete_task(self, task_id: int, user_id: str) -> Task:
        """
        Mark task as completed.
        
        [Task]: T029
        [Spec]: FR-001, FR-009
        
        Args:
            task_id: Task ID
            user_id: User ID
            
        Returns:
            Task: Completed task
            
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        logger.info("Completing task %s for user %s", task_id, user_id)
        
        task = await self.get_task(task_id, user_id)
        
        task.status = TaskStatusEnum.COMPLETED
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(task)
        
        # Publish event via Dapr
        await publish_task_event(
            event_type="completed",
            task_data=self._task_to_dict(task),
            user_id=user_id,
        )
        
        logger.info("Task completed: %s", task_id)
        
        return task
    
    async def delete_task(self, task_id: int, user_id: str) -> None:
        """
        Delete a task.
        
        [Task]: T030
        [Spec]: FR-001, FR-010
        
        Args:
            task_id: Task ID
            user_id: User ID
            
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        logger.info("Deleting task %s for user %s", task_id, user_id)
        
        task = await self.get_task(task_id, user_id)
        
        # Get task data before deletion for event
        task_data = self._task_to_dict(task)
        
        await self.db.delete(task)
        await self.db.commit()
        
        # Publish event via Dapr
        await publish_task_event(
            event_type="deleted",
            task_data=task_data,
            user_id=user_id,
        )
        
        logger.info("Task deleted: %s", task_id)
    
    async def list_tasks(
        self,
        user_id: str,
        query_params: Optional[TaskQueryParams] = None,
    ) -> List[Task]:
        """
        List tasks with optional filtering.
        
        [Task]: T027 (supporting)
        [Spec]: FR-001
        
        Args:
            user_id: User ID
            query_params: Optional query parameters for filtering
            
        Returns:
            List[Task]: List of tasks
        """
        logger.debug("Listing tasks for user %s", user_id)
        
        statement = select(Task).where(Task.user_id == user_id)
        
        # Apply filters
        if query_params:
            conditions = []
            
            if query_params.priority:
                conditions.append(Task.priority == query_params.priority)
            
            if query_params.status:
                conditions.append(Task.status == query_params.status)
            
            if query_params.is_recurring is not None:
                conditions.append(Task.is_recurring == query_params.is_recurring)
            
            if query_params.due_date_from:
                conditions.append(Task.due_date >= query_params.due_date_from)
            
            if query_params.due_date_to:
                conditions.append(Task.due_date <= query_params.due_date_to)
            
            if query_params.q:
                # Search in title and description
                search_pattern = f"%{query_params.q}%"
                conditions.append(
                    or_(
                        Task.title.ilike(search_pattern),
                        Task.description.ilike(search_pattern),
                    )
                )
            
            if conditions:
                statement = statement.where(and_(*conditions))
        
        # Apply sorting
        sort_column = getattr(Task, query_params.sort_by.value if query_params else "due_date")
        if query_params and query_params.sort_order.value == "desc":
            sort_column = sort_column.desc()
        statement = statement.order_by(sort_column)
        
        # Apply pagination
        if query_params:
            offset = (query_params.page - 1) * query_params.page_size
            statement = statement.offset(offset).limit(query_params.page_size)
        
        result = await self.db.execute(statement)
        tasks = result.scalars().all()
        
        return tasks
    
    async def _associate_tags(self, task: Task, tag_ids: List[int]) -> None:
        """
        Associate tags with a task.
        
        Args:
            task: Task to associate tags with
            tag_ids: List of tag IDs
        """
        for tag_id in tag_ids:
            task_tag = TaskTag(task_id=task.id, tag_id=tag_id)
            self.db.add(task_tag)
    
    async def _update_tags(self, task: Task, tag_ids: List[int]) -> None:
        """
        Update task tags (remove old, add new).
        
        Args:
            task: Task to update
            tag_ids: New list of tag IDs
        """
        # Remove existing associations
        statement = select(TaskTag).where(TaskTag.task_id == task.id)
        result = await self.db.execute(statement)
        existing_tags = result.scalars().all()
        
        for tag in existing_tags:
            await self.db.delete(tag)
        
        # Add new associations
        await self._associate_tags(task, tag_ids)
    
    def _task_to_dict(self, task: Task) -> dict:
        """
        Convert task to dictionary for event publishing.
        
        Args:
            task: Task to convert
            
        Returns:
            dict: Task data as dictionary
        """
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "priority": task.priority.value,
            "status": task.status.value,
            "is_recurring": task.is_recurring,
            "user_id": task.user_id,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }
