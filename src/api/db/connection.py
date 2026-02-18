"""
Database connection module for Phase V.

[Task]: T006
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Provides async PostgreSQL connection using sqlmodel.
Connection is managed via Dapr State component (not direct DB connections in business logic).
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import AsyncIterator
import sys

from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from api.config import settings


# Detect Python version for driver selection
PYTHON_VERSION = sys.version_info
USE_ASYNCPG = PYTHON_VERSION >= (3, 13)


def get_database_url() -> str:
    """
    Get database URL with appropriate driver for Python version.
    
    For Python 3.13+, uses asyncpg driver instead of psycopg2.
    
    Returns:
        str: Database URL with correct driver
    """
    if USE_ASYNCPG:
        # Convert postgresql:// to postgresql+asyncpg://
        return settings.database_url.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )
    else:
        # Use psycopg2 for older Python versions
        return settings.database_url.replace(
            "postgresql://", "postgresql+psycopg2://", 1
        )


class DatabaseConnection:
    """
    Database connection manager.
    
    Note: Per Constitution Principle I (Dapr-First Architecture),
    application code should use Dapr State API, not direct DB connections.
    This module is provided for Dapr component configuration and migrations.
    """
    
    def __init__(self):
        """Initialize database connection settings."""
        self.async_engine = None
        self.async_session_maker = None
        self._initialized = False
    
    async def connect(self) -> None:
        """
        Establish async database connection.
        
        Creates async engine and session maker for use with sqlmodel.
        """
        if self._initialized:
            return
        
        # Create async engine for PostgreSQL with appropriate driver
        database_url = get_database_url()
        self.async_engine = create_async_engine(
            database_url,
            echo=settings.log_level == "DEBUG",
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        
        # Create async session maker
        self.async_session_maker = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        self._initialized = True
    
    async def disconnect(self) -> None:
        """Close database connections."""
        if self.async_engine:
            await self.async_engine.dispose()
            self._initialized = False
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async database session context manager.
        
        Yields:
            AsyncSession: SQLAlchemy async session
            
        Example:
            async with db.get_session() as session:
                # use session
        """
        if not self._initialized:
            await self.connect()
        
        session = self.async_session_maker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def create_all_tables(self) -> None:
        """
        Create all database tables.
        
        WARNING: Only use for development/testing.
        Use migrations for production.
        """
        if not self._initialized:
            await self.connect()
        
        async with self.async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
    
    async def drop_all_tables(self) -> None:
        """
        Drop all database tables.
        
        WARNING: Destructive operation. Use with caution.
        """
        if not self._initialized:
            await self.connect()
        
        async with self.async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)


# Global database instance
db = DatabaseConnection()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency injection.
    
    Yields:
        AsyncSession: SQLAlchemy async session
        
    Usage:
        async with get_db_session() as session:
            # use session
    """
    async with db.get_session() as session:
        yield session
