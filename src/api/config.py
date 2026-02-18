"""
Application configuration module.

[Task]: T006 (supporting)
[From]: specs/001-phase5-cloud/tasks.md §Phase 2

Loads configuration from environment variables using pydantic-settings.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Per Constitution Principle VII (Security First), secrets are loaded from
    environment variables locally, and from Dapr Secrets API in production.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ============================================
    # Application Settings
    # ============================================
    app_name: str = "phase5-todo-app"
    app_env: str = "development"  # development, staging, production
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # ============================================
    # OpenAI API (for Chat/MCP)
    # ============================================
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    
    # ============================================
    # Database (Neon DB PostgreSQL)
    # ============================================
    database_url: str = ""
    
    # ============================================
    # Dapr Settings
    # ============================================
    dapr_http_port: int = 3500
    dapr_grpc_port: int = 50001
    dapr_app_id: str = "todo-backend"
    dapr_app_port: int = 8000
    
    @property
    def dapr_base_url(self) -> str:
        """Get Dapr HTTP API base URL."""
        return f"http://localhost:{self.dapr_http_port}/v1.0"
    
    @property
    def dapr_jobs_url(self) -> str:
        """Get Dapr Jobs API base URL."""
        return f"http://localhost:{self.dapr_http_port}/v1.0-alpha1"
    
    # ============================================
    # Kafka / Redpanda Cloud
    # ============================================
    redpanda_brokers: str = ""
    redpanda_username: str = ""
    redpanda_password: str = ""
    
    # Kafka Topics
    kafka_topic_task_events: str = "task-events"
    kafka_topic_reminders: str = "reminders"
    kafka_topic_task_updates: str = "task-updates"
    
    # ============================================
    # Reminder Settings
    # ============================================
    reminder_minutes_before: int = 30
    activity_retention_days: int = 90
    
    # ============================================
    # Kubernetes Settings
    # ============================================
    kubeconfig_path: Optional[str] = None
    k8s_namespace: str = "todo-app"
    k8s_dapr_namespace: str = "dapr-system"
    
    # ============================================
    # Validation
    # ============================================
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"
    
    def validate_settings(self) -> None:
        """
        Validate required settings are present.
        
        Raises:
            ValueError: If required settings are missing
        """
        errors = []
        
        if not self.database_url:
            errors.append("DATABASE_URL is required")
        
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        
        # Kafka/Redpanda credentials are optional for local development
        # but required for production
        if self.is_production and not self.redpanda_brokers:
            errors.append("REDPANDA_BROKERS is required in production")
        
        if errors:
            raise ValueError("; ".join(errors))


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings
        
    Usage:
        settings = get_settings()
    """
    settings = Settings()
    
    # Only validate in production
    if settings.is_production:
        settings.validate_settings()
    
    return settings


# Global settings instance
settings = get_settings()
