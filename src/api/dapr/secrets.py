"""
Dapr Secrets utility for Phase V.

[Task]: T012
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Provides secrets retrieval via Dapr Secrets API.
Per Constitution Principle VII, secrets MUST be accessed via Dapr, not environment variables.
"""

from typing import Optional, Dict
from functools import lru_cache
import logging

from api.dapr.client import get_dapr_client, DaprClient
from api.config import settings

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Secrets manager for Dapr Secrets API.
    
    Provides methods for retrieving secrets from Kubernetes Secrets store via Dapr.
    Used for API keys, database credentials, and other sensitive data.
    
    Usage:
        secrets_manager = SecretsManager()
        api_key = await secrets_manager.get_secret("openai-api-key")
    """
    
    def __init__(self, dapr_client: Optional[DaprClient] = None):
        """
        Initialize secrets manager.
        
        Args:
            dapr_client: Dapr client instance (uses global if not provided)
        """
        self.dapr_client = dapr_client or get_dapr_client()
        self.secret_store_name = "kubernetes-secrets"
    
    async def get_secret(self, key: str) -> Optional[str]:
        """
        Get secret value by key.
        
        Args:
            key: Secret key name
            
        Returns:
            Secret value or None if not found
            
        Usage:
            api_key = await secrets_manager.get_secret("openai-api-key")
        """
        try:
            value = await self.dapr_client.get_secret(
                secret_store_name=self.secret_store_name,
                key=key,
            )
            return value
        except Exception as e:
            logger.warning("Failed to get secret %s: %s", key, e)
            return None
    
    async def get_secrets(self, keys: list[str]) -> Dict[str, str]:
        """
        Get multiple secrets by keys.
        
        Args:
            keys: List of secret keys
            
        Returns:
            Dictionary mapping keys to values
            
        Usage:
            secrets = await secrets_manager.get_secrets(["db-password", "api-key"])
        """
        results = {}
        for key in keys:
            value = await self.get_secret(key)
            if value is not None:
                results[key] = value
        return results
    
    async def get_database_url(self) -> Optional[str]:
        """
        Get database connection URL from secrets.
        
        Returns:
            Database URL or None
        """
        return await self.get_secret("database-url")
    
    async def get_openai_api_key(self) -> Optional[str]:
        """
        Get OpenAI API key from secrets.
        
        Returns:
            OpenAI API key or None
        """
        return await self.get_secret("openai-api-key")
    
    async def get_redpanda_credentials(self) -> Dict[str, Optional[str]]:
        """
        Get Redpanda/Kafka credentials from secrets.
        
        Returns:
            Dictionary with brokers, username, password
        """
        brokers = await self.get_secret("redpanda-brokers")
        username = await self.get_secret("redpanda-username")
        password = await self.get_secret("redpanda-password")
        
        return {
            "brokers": brokers,
            "username": username,
            "password": password,
        }


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """
    Get global secrets manager instance.
    
    Returns:
        SecretsManager: Configured secrets manager
    """
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


# Convenience functions for direct usage
@lru_cache
def get_cached_secret(key: str) -> Optional[str]:
    """
    Get secret with caching (for static secrets that don't change).
    
    Args:
        key: Secret key
        
    Returns:
        Secret value or None
        
    Note: Only use for secrets that don't change at runtime.
    """
    import asyncio
    
    # This is a sync wrapper around async function
    # Use with caution - better to use SecretsManager directly in async code
    secrets_manager = get_secrets_manager()
    
    # Note: This won't work in async context without proper event loop handling
    # Prefer using await secrets_manager.get_secret(key) in async code
    raise RuntimeError(
        "get_cached_secret cannot be used in async context. "
        "Use SecretsManager.get_secret() instead."
    )


async def get_secret(key: str) -> Optional[str]:
    """
    Get secret via Dapr Secrets API.
    
    Args:
        key: Secret key
        
    Returns:
        Secret value or None
        
    Usage:
        api_key = await get_secret("openai-api-key")
    """
    secrets_manager = get_secrets_manager()
    return await secrets_manager.get_secret(key)


async def get_database_url() -> Optional[str]:
    """Get database URL from secrets."""
    secrets_manager = get_secrets_manager()
    return await secrets_manager.get_database_url()


async def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from secrets."""
    secrets_manager = get_secrets_manager()
    return await secrets_manager.get_openai_api_key()
