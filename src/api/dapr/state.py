"""
Dapr State management utility for Phase V.

[Task]: T010
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Provides state management via Dapr State API.
Per Constitution Principle I, all state interactions MUST go through Dapr.
"""

from typing import Any, Optional, Dict, List
from datetime import datetime
import logging

from api.dapr.client import get_dapr_client, DaprClient
from api.config import settings

logger = logging.getLogger(__name__)


class StateManager:
    """
    State manager for Dapr State Store.
    
    Provides methods for storing and retrieving state via Dapr.
    Used for conversation state, task cache, and other application state.
    
    Usage:
        state_manager = StateManager()
        await state_manager.save("conversation-123", {"messages": [...]})
        data = await state_manager.get("conversation-123")
    """
    
    def __init__(self, dapr_client: Optional[DaprClient] = None):
        """
        Initialize state manager.
        
        Args:
            dapr_client: Dapr client instance (uses global if not provided)
        """
        self.dapr_client = dapr_client or get_dapr_client()
        self.state_store_name = "statestore"
    
    async def get(
        self,
        key: str,
        consistency: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Get value from state store.
        
        Args:
            key: State key
            consistency: Consistency level ("strong" or "eventual")
            
        Returns:
            State value or None if not found
            
        Usage:
            value = await state_manager.get("conversation-123")
        """
        try:
            value = await self.dapr_client.get_state(
                state_store_name=self.state_store_name,
                key=key,
                consistency=consistency,
            )
            return value
        except Exception as e:
            logger.warning("Failed to get state for key %s: %s", key, e)
            return None
    
    async def save(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Save value to state store.
        
        Args:
            key: State key
            value: State value
            
        Usage:
            await state_manager.save("conversation-123", {"messages": [...]})
        """
        await self.dapr_client.save_state(
            state_store_name=self.state_store_name,
            key=key,
            value=value,
        )
        
        logger.info("Saved state for key: %s", key)
    
    async def delete(self, key: str) -> None:
        """
        Delete value from state store.
        
        Args:
            key: State key
        """
        await self.dapr_client.delete_state(
            state_store_name=self.state_store_name,
            key=key,
        )
        
        logger.info("Deleted state for key: %s", key)
    
    async def get_bulk(
        self,
        keys: List[str],
    ) -> Dict[str, Any]:
        """
        Get multiple values from state store.
        
        Args:
            keys: List of state keys
            
        Returns:
            Dictionary mapping keys to values
            
        Usage:
            values = await state_manager.get_bulk(["key1", "key2", "key3"])
        """
        results = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results[key] = value
        return results
    
    async def save_bulk(
        self,
        items: Dict[str, Any],
    ) -> None:
        """
        Save multiple values to state store.
        
        Args:
            items: Dictionary mapping keys to values
            
        Usage:
            await state_manager.save_bulk({"key1": value1, "key2": value2})
        """
        for key, value in items.items():
            await self.save(key, value)
        
        logger.info("Saved %d state items", len(items))
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in state store.
        
        Args:
            key: State key
            
        Returns:
            True if key exists
        """
        value = await self.get(key)
        return value is not None
    
    async def get_with_metadata(
        self,
        key: str,
    ) -> Dict[str, Any]:
        """
        Get value with metadata (created_at, updated_at).
        
        Args:
            key: State key
            
        Returns:
            Dictionary with value and metadata
        """
        value = await self.get(key)
        
        if value is None:
            return {"exists": False}
        
        return {
            "exists": True,
            "value": value,
            "key": key,
            "retrieved_at": datetime.utcnow().isoformat() + "Z",
        }


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """
    Get global state manager instance.
    
    Returns:
        StateManager: Configured state manager
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


# Convenience functions for direct usage
async def save_state(key: str, value: Any) -> None:
    """
    Save state via Dapr State API.
    
    Args:
        key: State key
        value: State value
        
    Usage:
        await save_state("conversation-123", {"messages": [...]})
    """
    state_manager = get_state_manager()
    await state_manager.save(key, value)


async def get_state(key: str) -> Optional[Any]:
    """
    Get state via Dapr State API.
    
    Args:
        key: State key
        
    Returns:
        State value or None
    """
    state_manager = get_state_manager()
    return await state_manager.get(key)


async def delete_state(key: str) -> None:
    """
    Delete state via Dapr State API.
    
    Args:
        key: State key
    """
    state_manager = get_state_manager()
    await state_manager.delete(key)
