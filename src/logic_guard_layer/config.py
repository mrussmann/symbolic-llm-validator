"""Configuration management for Logic-Guard-Layer."""

import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenRouter LLM Configuration
    openrouter_api_key: str = Field(
        default="",
        alias="OPENROUTER_API_KEY",
        description="OpenRouter API key"
    )

    # Admin Authentication (MUST be set via environment variables)
    admin_username: str = Field(
        default="",
        alias="ADMIN_USERNAME",
        description="Admin username for authentication"
    )
    admin_password: str = Field(
        default="",
        alias="ADMIN_PASSWORD",
        description="Admin password for authentication"
    )

    # Session Security
    session_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        alias="SESSION_SECRET_KEY",
        description="Secret key for session signing"
    )
    session_max_age: int = Field(
        default=3600,  # 1 hour
        alias="SESSION_MAX_AGE",
        description="Session timeout in seconds"
    )

    # CORS Configuration
    cors_origins: str = Field(
        default="",
        alias="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins (empty = same-origin only)"
    )

    # Rate Limiting
    rate_limit_requests: int = Field(
        default=100,
        alias="RATE_LIMIT_REQUESTS",
        description="Maximum requests per rate limit window"
    )
    rate_limit_window: int = Field(
        default=60,
        alias="RATE_LIMIT_WINDOW",
        description="Rate limit window in seconds"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
        description="OpenRouter API base URL"
    )
    openrouter_model: str = Field(
        default="tngtech/deepseek-r1t2-chimera:free",
        alias="OPENROUTER_MODEL",
        description="Default LLM model to use"
    )
    llm_timeout: float = Field(
        default=60.0,
        alias="LLM_TIMEOUT",
        description="Timeout for LLM API calls in seconds"
    )
    llm_max_retries: int = Field(
        default=3,
        alias="LLM_MAX_RETRIES",
        description="Maximum retries for LLM API calls"
    )

    # Ontology Configuration
    ontology_path: str = Field(
        default="",
        alias="ONTOLOGY_PATH",
        description="Path to the OWL ontology file"
    )

    # Self-Correction Loop Settings
    max_correction_iterations: int = Field(
        default=5,
        alias="MAX_ITERATIONS",
        description="Maximum iterations for self-correction loop"
    )
    llm_temperature: float = Field(
        default=0.0,
        alias="LLM_TEMPERATURE",
        description="Temperature for LLM sampling (0 for deterministic)"
    )

    # Application Settings
    app_name: str = "Logic-Guard-Layer"
    app_version: str = "1.0.0"
    debug: bool = Field(
        default=False,
        alias="DEBUG",
        description="Enable debug mode"
    )

    # Server Settings
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def get_ontology_path(self) -> Path:
        """Get the resolved ontology path."""
        if self.ontology_path:
            return Path(self.ontology_path)

        # Try to find ontology in package data directory
        package_dir = Path(__file__).parent
        default_path = package_dir / "data" / "maintenance.owl"

        if default_path.exists():
            return default_path

        # Fallback to current directory
        return Path("data/maintenance.owl")

    def get_cors_origins(self) -> List[str]:
        """Get list of allowed CORS origins."""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def is_admin_configured(self) -> bool:
        """Check if admin credentials are properly configured."""
        return bool(self.admin_username and self.admin_password)

    def validate_security_config(self) -> List[str]:
        """Validate security configuration and return list of warnings."""
        warnings = []

        if not self.admin_username or not self.admin_password:
            warnings.append("ADMIN_USERNAME and ADMIN_PASSWORD not set - admin features disabled")

        if not self.openrouter_api_key:
            warnings.append("OPENROUTER_API_KEY not set - LLM features will fail")

        if self.debug:
            warnings.append("DEBUG mode is enabled - disable in production")

        if not self.cors_origins and not self.debug:
            warnings.append("CORS_ORIGINS not set - only same-origin requests allowed")

        return warnings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
