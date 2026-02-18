"""
Phase V API package.

[Task]: T006 (supporting)
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Note: Import lazily to avoid circular dependencies and initialization order issues.
"""


def get_settings():
    """Lazy import settings to avoid initialization order issues."""
    from api.config import settings
    return settings


def get_db():
    """Lazy import db to avoid initialization order issues."""
    from api.db.connection import db
    return db


def get_db_session():
    """Lazy import get_db_session to avoid initialization order issues."""
    from api.db.connection import get_db_session
    return get_db_session


# Lazy imports to avoid initialization issues
__all__ = ["get_settings", "get_db", "get_db_session"]
