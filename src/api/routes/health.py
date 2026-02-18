"""
Health check endpoints for Phase V.

[Task]: T016
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Provides /health and /ready endpoints for Kubernetes health checks.
Includes dependency checks for Dapr, Kafka, and Database.
"""

from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from api.db.connection import db
from api.dapr.client import get_dapr_client, DaprError
from api.config import settings
from api.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ============================================
# Response Models
# ============================================


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Overall health status (healthy/unhealthy)")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    version: str = Field(..., description="Application version")
    app_name: str = Field(..., description="Application name")
    app_env: str = Field(..., description="Application environment")


class DependencyStatus(BaseModel):
    """Dependency health status."""
    
    status: str = Field(..., description="Dependency status (healthy/unhealthy/unreachable)")
    latency_ms: Optional[float] = Field(None, description="Response latency in milliseconds")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response with dependency status."""
    
    dependencies: Dict[str, DependencyStatus] = Field(
        ..., description="Dependency health status"
    )


# ============================================
# Health Check Handlers
# ============================================


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.
    
    Returns 200 OK if application is running.
    Does not check dependencies - use /ready for readiness probes.
    
    Returns:
        HealthResponse: Basic health status
        
    Usage:
        GET /health
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0",
        app_name=settings.app_name,
        app_env=settings.app_env,
    )


@router.get(
    "/ready",
    response_model=DetailedHealthResponse,
    tags=["Health"],
    status_code=status.HTTP_200_OK,
)
async def readiness_check() -> DetailedHealthResponse:
    """
    Readiness check endpoint with dependency health.
    
    Checks health of:
    - Database connection
    - Dapr sidecar
    - Kafka (via Dapr Pub/Sub)
    
    Returns 200 OK only if all dependencies are healthy.
    Use for Kubernetes readiness probes.
    
    Returns:
        DetailedHealthResponse: Health status with dependency details
        
    Raises:
        HTTPException: 503 if any dependency is unhealthy
        
    Usage:
        GET /ready
    """
    dependencies: Dict[str, DependencyStatus] = {}
    all_healthy = True
    
    # Check database
    db_status = await check_database()
    dependencies["database"] = db_status
    if db_status.status != "healthy":
        all_healthy = False
    
    # Check Dapr sidecar
    dapr_status = await check_dapr()
    dependencies["dapr"] = dapr_status
    if dapr_status.status != "healthy":
        all_healthy = False
    
    # Check Kafka (via Dapr)
    kafka_status = await check_kafka()
    dependencies["kafka"] = kafka_status
    if kafka_status.status != "healthy":
        all_healthy = False
    
    # Build response
    response = DetailedHealthResponse(
        status="healthy" if all_healthy else "unhealthy",
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0",
        app_name=settings.app_name,
        app_env=settings.app_env,
        dependencies=dependencies,
    )
    
    if not all_healthy:
        logger.warning(
            "Health check failed",
            extra={"dependencies": dependencies},
        )
    
    return response


# ============================================
# Dependency Check Functions
# ============================================


async def check_database() -> DependencyStatus:
    """
    Check database connectivity.
    
    Returns:
        DependencyStatus: Database health status
    """
    import time
    
    start_time = time.time()
    
    try:
        # Test database connection with simple query
        async with db.get_session() as session:
            await session.execute("SELECT 1")
        
        latency_ms = (time.time() - start_time) * 1000
        
        return DependencyStatus(
            status="healthy",
            latency_ms=latency_ms,
        )
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return DependencyStatus(
            status="unreachable",
            error=str(e),
        )


async def check_dapr() -> DependencyStatus:
    """
    Check Dapr sidecar connectivity.
    
    Returns:
        DependencyStatus: Dapr health status
    """
    import time
    
    start_time = time.time()
    
    try:
        dapr_client = get_dapr_client()
        await dapr_client.health_check()
        
        latency_ms = (time.time() - start_time) * 1000
        
        return DependencyStatus(
            status="healthy",
            latency_ms=latency_ms,
        )
    except DaprError as e:
        logger.error("Dapr health check failed: %s", e)
        return DependencyStatus(
            status="unreachable",
            error=str(e),
        )
    except Exception as e:
        logger.error("Dapr health check failed with unexpected error: %s", e)
        return DependencyStatus(
            status="unreachable",
            error=str(e),
        )


async def check_kafka() -> DependencyStatus:
    """
    Check Kafka connectivity via Dapr Pub/Sub.
    
    Returns:
        DependencyStatus: Kafka health status
    """
    import time
    
    start_time = time.time()
    
    try:
        # Test Kafka connectivity by publishing a test event
        from api.dapr.publisher import get_event_publisher
        
        publisher = get_event_publisher()
        await publisher.publish(
            topic="task-events",
            event_type="health.check",
            data={"message": "Health check"},
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return DependencyStatus(
            status="healthy",
            latency_ms=latency_ms,
        )
    except Exception as e:
        logger.error("Kafka health check failed: %s", e)
        return DependencyStatus(
            status="unreachable",
            error=str(e),
        )


# ============================================
# Liveness Check (simpler than readiness)
# ============================================


@router.get("/live", response_model=HealthResponse, tags=["Health"])
async def liveness_check() -> HealthResponse:
    """
    Liveness check endpoint.
    
    Returns 200 OK if application process is running.
    Simpler than /health - doesn't check any dependencies.
    Use for Kubernetes liveness probes.
    
    Returns:
        HealthResponse: Basic health status
        
    Usage:
        GET /live
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0",
        app_name=settings.app_name,
        app_env=settings.app_env,
    )
