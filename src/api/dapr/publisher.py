"""
Dapr Pub/Sub publisher utility for Phase V.

[Task]: T009
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Provides simplified event publishing via Dapr Pub/Sub.
Per Constitution Principle I, all Kafka interactions MUST go through Dapr.
"""

from typing import Any, Dict, Optional
from datetime import datetime
import logging

from api.dapr.client import get_dapr_client, DaprClient
from api.config import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Event publisher for Dapr Pub/Sub.
    
    Provides methods for publishing events to Kafka topics via Dapr.
    All task operations should publish events through this class.
    
    Usage:
        publisher = EventPublisher()
        await publisher.publish_task_event("created", task_data, user_id)
    """
    
    def __init__(self, dapr_client: Optional[DaprClient] = None):
        """
        Initialize event publisher.
        
        Args:
            dapr_client: Dapr client instance (uses global if not provided)
        """
        self.dapr_client = dapr_client or get_dapr_client()
        self.pubsub_name = "kafka-pubsub"
    
    async def publish(
        self,
        topic: str,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Publish event to Dapr Pub/Sub.
        
        Args:
            topic: Kafka topic name
            event_type: Type of event (e.g., "created", "updated", "completed")
            data: Event payload
            metadata: Optional metadata
            
        Raises:
            DaprError: If publishing fails
        """
        event_data = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **data,
        }
        
        await self.dapr_client.publish(
            pubsub_name=self.pubsub_name,
            topic=topic,
            data=event_data,
            metadata=metadata,
        )
        
        logger.info(
            "Published event to %s: %s",
            topic,
            event_type,
            extra={"event_type": event_type, "topic": topic},
        )
    
    async def publish_task_event(
        self,
        event_type: str,
        task_data: Dict[str, Any],
        user_id: str,
    ) -> None:
        """
        Publish task event to task-events topic.
        
        Args:
            event_type: Event type (created, updated, completed, deleted)
            task_data: Full task object
            user_id: User who performed the action
            
        Usage:
            await publisher.publish_task_event("created", task_dict, user_id)
        """
        data = {
            "task_id": task_data.get("id"),
            "task_data": task_data,
            "user_id": user_id,
        }
        
        await self.publish(
            topic=settings.kafka_topic_task_events,
            event_type=event_type,
            data=data,
        )
    
    async def publish_reminder_event(
        self,
        task_id: int,
        title: str,
        due_at: datetime,
        remind_at: datetime,
        user_id: str,
    ) -> None:
        """
        Publish reminder event to reminders topic.
        
        Args:
            task_id: Task ID
            title: Task title for notification
            due_at: When task is due
            remind_at: When to send reminder
            user_id: User to notify
            
        Usage:
            await publisher.publish_reminder_event(task_id, title, due_at, remind_at, user_id)
        """
        data = {
            "task_id": task_id,
            "title": title,
            "due_at": due_at.isoformat() + "Z",
            "remind_at": remind_at.isoformat() + "Z",
            "user_id": user_id,
        }
        
        await self.publish(
            topic=settings.kafka_topic_reminders,
            event_type="reminder.due",
            data=data,
        )
    
    async def publish_task_update_event(
        self,
        event_type: str,
        task_data: Dict[str, Any],
        user_id: str,
    ) -> None:
        """
        Publish task update event to task-updates topic for real-time sync.
        
        Args:
            event_type: Event type (created, updated, completed, deleted)
            task_data: Full task object
            user_id: User who performed the action
            
        Usage:
            await publisher.publish_task_update_event("updated", task_dict, user_id)
        """
        data = {
            "task_id": task_data.get("id"),
            "task_data": task_data,
            "user_id": user_id,
        }
        
        await self.publish(
            topic=settings.kafka_topic_task_updates,
            event_type=event_type,
            data=data,
        )


# Global publisher instance
_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """
    Get global event publisher instance.
    
    Returns:
        EventPublisher: Configured event publisher
    """
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher


# Convenience functions for direct usage
async def publish_event(topic: str, event_type: str, data: Dict[str, Any]) -> None:
    """
    Publish event via Dapr Pub/Sub.
    
    Args:
        topic: Kafka topic name
        event_type: Event type
        data: Event payload
        
    Usage:
        await publish_event("task-events", "created", {"task_id": 123})
    """
    publisher = get_event_publisher()
    await publisher.publish(topic, event_type, data)


async def publish_task_event(event_type: str, task_data: Dict, user_id: str) -> None:
    """Publish task event to task-events topic."""
    publisher = get_event_publisher()
    await publisher.publish_task_event(event_type, task_data, user_id)


async def publish_reminder_event(
    task_id: int, title: str, due_at: datetime, remind_at: datetime, user_id: str
) -> None:
    """Publish reminder event to reminders topic."""
    publisher = get_event_publisher()
    await publisher.publish_reminder_event(task_id, title, due_at, remind_at, user_id)


async def publish_task_update_event(event_type: str, task_data: Dict, user_id: str) -> None:
    """Publish task update event to task-updates topic."""
    publisher = get_event_publisher()
    await publisher.publish_task_update_event(event_type, task_data, user_id)
