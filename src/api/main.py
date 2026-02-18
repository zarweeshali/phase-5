"""
FastAPI application factory for Phase V.

[Task]: T015
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Creates FastAPI application with lifespan context manager for DB connection.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import sys
import os

# Add src directory to Python path for imports
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.db.connection import db
from api.logging_config import setup_logging, get_logger
from api.dapr.client import get_dapr_client


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events:
    - Startup: Initialize logging
    - Shutdown: Close database connections, Dapr client

    Note: Database and Dapr connections are lazy (initialized on first use)
    to allow server startup even without DB/Dapr available.

    Args:
        app: FastAPI application instance

    Yields:
        None

    Usage:
        app = create_app()
        # lifespan runs on startup and shutdown
    """
    # Startup
    logger.info("Starting up application", extra={"app_name": settings.app_name})

    # Setup logging
    setup_logging()

    # Note: Database and Dapr connections are lazy-initialized on first use
    # to allow server startup without requiring DB/Dapr to be available

    logger.info(
        "Application startup complete",
        extra={
            "app_name": settings.app_name,
            "app_env": settings.app_env,
            "dapr_app_id": settings.dapr_app_id,
        },
    )

    yield

    # Shutdown
    logger.info("Shutting down application")
    
    # Close Dapr client
    await dapr_client.disconnect()
    
    # Close database connection
    await db.disconnect()
    
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Create FastAPI application instance.
    
    Configures:
    - Lifespan events (startup/shutdown)
    - CORS middleware
    - Routes registration
    
    Returns:
        FastAPI: Configured application instance
        
    Usage:
        app = create_app()
    """
    app = FastAPI(
        title=settings.app_name,
        description="Phase V: Advanced Cloud Deployment - Todo App with Kafka and Dapr",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure per environment in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routes
    register_routes(app)
    
    logger.info("FastAPI application created", extra={"app_name": settings.app_name})
    
    return app


def register_routes(app: FastAPI) -> None:
    """
    Register application routes.
    
    Args:
        app: FastAPI application instance
        
    Note:
        Routes are imported and registered here to avoid circular imports.
    """
    from api.routes import health
    from api.routes import tasks
    
    # Register health check routes
    app.include_router(health.router, tags=["Health"])
    
    # Register task routes
    app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
    
    # TODO: Register jobs routes (Phase 5)
    # from api.routes import jobs
    # app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
    
    # TODO: Register MCP routes
    # from api.routes import mcp
    # app.include_router(mcp.router, tags=["MCP"])
    
    logger.info("Routes registered")


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=settings.dapr_app_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
