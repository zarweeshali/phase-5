"""
Dapr Jobs scheduler utility for Phase V.

[Task]: T011
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Provides job scheduling via Dapr Jobs API.
Used for scheduling reminders at exact times.
"""

from typing import Any, Dict, Optional
from datetime import datetime
import logging

from api.dapr.client import get_dapr_client, DaprClient
from api.config import settings

logger = logging.getLogger(__name__)


class JobScheduler:
    """
    Job scheduler for Dapr Jobs API.
    
    Provides methods for scheduling and canceling jobs.
    Used for scheduling reminders at exact times.
    
    Usage:
        scheduler = JobScheduler()
        await scheduler.schedule_job("reminder-123", due_time, {"task_id": 123})
    """
    
    def __init__(self, dapr_client: Optional[DaprClient] = None):
        """
        Initialize job scheduler.
        
        Args:
            dapr_client: Dapr client instance (uses global if not provided)
        """
        self.dapr_client = dapr_client or get_dapr_client()
        self.callback_path = "/api/jobs/trigger"
    
    async def schedule_job(
        self,
        job_id: str,
        due_time: datetime,
        data: Dict[str, Any],
        period: Optional[str] = None,
        ttl: Optional[str] = None,
    ) -> None:
        """
        Schedule a job to fire at a specific time.
        
        Args:
            job_id: Unique job identifier (e.g., "reminder-task-123")
            due_time: When to fire the job (datetime object)
            data: Job payload (sent to callback endpoint)
            period: Optional recurrence period (e.g., "R5/PT1H" for 5 repetitions every hour)
            ttl: Optional time-to-live for the job
            
        Usage:
            # Schedule one-time reminder
            await scheduler.schedule_job(
                "reminder-123",
                datetime(2026, 2, 18, 16, 30, 0),
                {"task_id": 123, "user_id": "abc", "type": "reminder"}
            )
            
            # Schedule recurring job
            await scheduler.schedule_job(
                "daily-cleanup",
                datetime(2026, 2, 18, 0, 0, 0),
                {"type": "cleanup"},
                period="R365/PT24H"  # 365 repetitions, every 24 hours
            )
        """
        due_time_str = due_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        await self.dapr_client.schedule_job(
            job_id=job_id,
            due_time=due_time_str,
            data=data,
            period=period,
            ttl=ttl,
        )
        
        logger.info(
            "Scheduled job %s for %s",
            job_id,
            due_time_str,
            extra={"job_id": job_id, "due_time": due_time_str},
        )
    
    async def schedule_reminder(
        self,
        task_id: int,
        remind_at: datetime,
        user_id: str,
        title: str,
    ) -> None:
        """
        Schedule a reminder job.
        
        Convenience method for scheduling task reminders.
        
        Args:
            task_id: Task ID
            remind_at: When to send reminder
            user_id: User ID
            title: Task title
            
        Usage:
            await scheduler.schedule_reminder(task_id, remind_at, user_id, "Submit report")
        """
        job_id = f"reminder-task-{task_id}"
        
        data = {
            "task_id": task_id,
            "user_id": user_id,
            "title": title,
            "type": "reminder",
        }
        
        await self.schedule_job(
            job_id=job_id,
            due_time=remind_at,
            data=data,
        )
    
    async def cancel_job(self, job_id: str) -> None:
        """
        Cancel a scheduled job.
        
        Args:
            job_id: Job identifier to cancel
            
        Usage:
            await scheduler.cancel_job("reminder-123")
        """
        await self.dapr_client.cancel_job(job_id=job_id)
        
        logger.info("Cancelled job: %s", job_id)
    
    async def cancel_reminder(self, task_id: int) -> None:
        """
        Cancel a reminder job.
        
        Args:
            task_id: Task ID
        """
        job_id = f"reminder-task-{task_id}"
        await self.cancel_job(job_id)
    
    async def reschedule_reminder(
        self,
        task_id: int,
        remind_at: datetime,
        user_id: str,
        title: str,
    ) -> None:
        """
        Reschedule a reminder (cancel and create new).
        
        Args:
            task_id: Task ID
            remind_at: New reminder time
            user_id: User ID
            title: Task title
        """
        # Cancel existing reminder
        await self.cancel_reminder(task_id)
        
        # Schedule new reminder
        await self.schedule_reminder(task_id, remind_at, user_id, title)


# Global job scheduler instance
_scheduler: Optional[JobScheduler] = None


def get_job_scheduler() -> JobScheduler:
    """
    Get global job scheduler instance.
    
    Returns:
        JobScheduler: Configured job scheduler
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler


# Convenience functions for direct usage
async def schedule_job(
    job_id: str, due_time: datetime, data: Dict[str, Any], period: Optional[str] = None
) -> None:
    """
    Schedule a job via Dapr Jobs API.
    
    Args:
        job_id: Unique job identifier
        due_time: When to fire the job
        data: Job payload
        period: Optional recurrence period
    """
    scheduler = get_job_scheduler()
    await scheduler.schedule_job(job_id, due_time, data, period)


async def schedule_reminder(task_id: int, remind_at: datetime, user_id: str, title: str) -> None:
    """Schedule a reminder job."""
    scheduler = get_job_scheduler()
    await scheduler.schedule_reminder(task_id, remind_at, user_id, title)


async def cancel_job(job_id: str) -> None:
    """Cancel a scheduled job."""
    scheduler = get_job_scheduler()
    await scheduler.cancel_job(job_id)


async def cancel_reminder(task_id: int) -> None:
    """Cancel a reminder job."""
    scheduler = get_job_scheduler()
    await scheduler.cancel_reminder(task_id)
