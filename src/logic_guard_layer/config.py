"""Configuration management for Logic-Guard-Layer."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenRouter LLM Configuration
    openrouter_api_key: str = Field(
        default="",
        alias="OPENROUTER_API_KEY",
        description="OpenRouter API key"
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


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
