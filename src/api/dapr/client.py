"""
Dapr client wrapper for Phase V.

[Task]: T008
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Provides HTTP client for Dapr sidecar communication.
Per Constitution Principle I, all infrastructure interactions MUST go through Dapr.
"""

import httpx
from typing import Optional, Any, Dict
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from api.config import settings


class DaprClient:
    """
    Async HTTP client for Dapr sidecar communication.
    
    Provides methods for:
    - Pub/Sub publishing
    - State management
    - Jobs scheduling
    - Secrets retrieval
    - Service invocation
    
    Usage:
        async with DaprClient() as client:
            await client.publish_event("topic", data)
    """
    
    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize Dapr client.
        
        Args:
            base_url: Dapr HTTP API base URL (default: from settings)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.dapr_base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def connect(self) -> None:
        """Establish connection to Dapr sidecar."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={"Content-Type": "application/json"},
            )
    
    async def disconnect(self) -> None:
        """Close connection to Dapr sidecar."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """
        Get HTTP client context manager.
        
        Yields:
            httpx.AsyncClient: Configured HTTP client
            
        Usage:
            async with client.get_client() as http:
                response = await http.get("/healthz")
        """
        if self._client is None:
            await self.connect()
        
        try:
            yield self._client
        except httpx.HTTPError as e:
            # Log error with correlation ID (if available)
            raise DaprError(f"Dapr HTTP error: {e}") from e
    
    async def health_check(self) -> bool:
        """
        Check if Dapr sidecar is healthy.
        
        Returns:
            bool: True if sidecar is healthy
            
        Raises:
            DaprError: If sidecar is unreachable
        """
        async with self.get_client() as http:
            try:
                response = await http.get("/healthz")
                response.raise_for_status()
                return True
            except httpx.HTTPError as e:
                raise DaprError(f"Dapr sidecar health check failed: {e}") from e
    
    async def publish(
        self,
        pubsub_name: str,
        topic: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Publish event to Dapr Pub/Sub.
        
        Args:
            pubsub_name: Dapr pubsub component name (e.g., "kafka-pubsub")
            topic: Topic to publish to
            data: Event data to publish
            metadata: Optional metadata for the event
            
        Usage:
            await client.publish("kafka-pubsub", "task-events", {"event_type": "created"})
        """
        async with self.get_client() as http:
            url = f"/publish/{pubsub_name}/{topic}"
            
            payload: Dict[str, Any] = {"data": data}
            if metadata:
                payload["metadata"] = metadata
            
            response = await http.post(url, json=payload)
            response.raise_for_status()
    
    async def get_state(
        self,
        state_store_name: str,
        key: str,
        consistency: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Get state from Dapr State Store.
        
        Args:
            state_store_name: Dapr state store component name
            key: State key
            consistency: Consistency level ("strong" or "eventual")
            
        Returns:
            State value or None if not found
            
        Usage:
            value = await client.get_state("statestore", "conversation-123")
        """
        async with self.get_client() as http:
            url = f"/state/{state_store_name}/{key}"
            params = {}
            if consistency:
                params["consistency"] = consistency
            
            response = await http.get(url, params=params)
            response.raise_for_status()
            
            if response.status_code == 204:
                return None
            
            return response.json()
    
    async def save_state(
        self,
        state_store_name: str,
        key: str,
        value: Any,
    ) -> None:
        """
        Save state to Dapr State Store.
        
        Args:
            state_store_name: Dapr state store component name
            key: State key
            value: State value
            
        Usage:
            await client.save_state("statestore", "conversation-123", {"messages": [...]})
        """
        async with self.get_client() as http:
            url = f"/state/{state_store_name}"
            
            payload = [
                {
                    "key": key,
                    "value": value,
                }
            ]
            
            response = await http.post(url, json=payload)
            response.raise_for_status()
    
    async def delete_state(
        self,
        state_store_name: str,
        key: str,
    ) -> None:
        """
        Delete state from Dapr State Store.
        
        Args:
            state_store_name: Dapr state store component name
            key: State key
        """
        async with self.get_client() as http:
            url = f"/state/{state_store_name}/{key}"
            response = await http.delete(url)
            response.raise_for_status()
    
    async def get_secret(
        self,
        secret_store_name: str,
        key: str,
    ) -> Optional[str]:
        """
        Get secret from Dapr Secrets Store.
        
        Args:
            secret_store_name: Dapr secrets store component name
            key: Secret key
            
        Returns:
            Secret value or None if not found
            
        Usage:
            api_key = await client.get_secret("kubernetes-secrets", "openai-api-key")
        """
        async with self.get_client() as http:
            url = f"/secrets/{secret_store_name}/{key}"
            response = await http.get(url)
            response.raise_for_status()
            
            data = response.json()
            return data.get(key)
    
    async def schedule_job(
        self,
        job_id: str,
        due_time: str,
        data: Dict[str, Any],
        period: Optional[str] = None,
        ttl: Optional[str] = None,
    ) -> None:
        """
        Schedule a job using Dapr Jobs API.
        
        Args:
            job_id: Unique job identifier
            due_time: When to fire the job (ISO 8601 format or time duration)
            data: Job payload (sent to callback endpoint)
            period: Optional recurrence period (e.g., "R5/PT1H" for 5 repetitions every hour)
            ttl: Optional time-to-live for the job
            
        Usage:
            await client.schedule_job(
                "reminder-123",
                "2026-02-18T16:30:00Z",
                {"task_id": 123, "user_id": "user-abc"}
            )
        """
        async with self.get_client() as http:
            url = f"/jobs/{job_id}"
            
            payload: Dict[str, Any] = {
                "dueTime": due_time,
                "data": data,
            }
            
            if period:
                payload["period"] = period
            
            if ttl:
                payload["ttl"] = ttl
            
            response = await http.post(url, json=payload)
            response.raise_for_status()
    
    async def cancel_job(self, job_id: str) -> None:
        """
        Cancel a scheduled job.
        
        Args:
            job_id: Job identifier to cancel
        """
        async with self.get_client() as http:
            url = f"/jobs/{job_id}"
            response = await http.delete(url)
            response.raise_for_status()
    
    async def invoke_service(
        self,
        app_id: str,
        method: str,
        http_verb: str = "POST",
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Invoke another service via Dapr Service Invocation.
        
        Args:
            app_id: Target service Dapr app ID
            method: Method/endpoint to invoke
            http_verb: HTTP method (GET, POST, PUT, DELETE)
            data: Request payload
            
        Returns:
            Response data
            
        Usage:
            result = await client.invoke_service(
                "notification-service",
                "api/notify",
                "POST",
                {"user_id": "abc", "message": "Hello"}
            )
        """
        async with self.get_client() as http:
            url = f"/invoke/{app_id}/method/{method}"
            
            if http_verb.upper() == "GET":
                response = await http.get(url)
            elif http_verb.upper() == "POST":
                response = await http.post(url, json=data or {})
            elif http_verb.upper() == "PUT":
                response = await http.put(url, json=data or {})
            elif http_verb.upper() == "DELETE":
                response = await http.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP verb: {http_verb}")
            
            response.raise_for_status()
            
            if response.status_code == 204:
                return None
            
            return response.json()


class DaprError(Exception):
    """Exception raised for Dapr-related errors."""
    
    pass


# Global Dapr client instance (lazy initialization)
_dapr_client: Optional[DaprClient] = None


def get_dapr_client() -> DaprClient:
    """
    Get global Dapr client instance.
    
    Returns:
        DaprClient: Configured Dapr client
    """
    global _dapr_client
    if _dapr_client is None:
        _dapr_client = DaprClient()
    return _dapr_client
