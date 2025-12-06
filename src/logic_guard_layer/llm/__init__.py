"""LLM integration modules."""

from logic_guard_layer.llm.client import (
    OpenRouterClient,
    OpenRouterConfig,
    LLMError,
    create_client_from_settings,
)
from logic_guard_layer.llm.prompts import (
    get_parsing_prompt,
    get_correction_prompt,
    get_extraction_schema,
    PARSING_SYSTEM_PROMPT,
    CORRECTION_SYSTEM_PROMPT,
)

__all__ = [
    "OpenRouterClient",
    "OpenRouterConfig",
    "LLMError",
    "create_client_from_settings",
    "get_parsing_prompt",
    "get_correction_prompt",
    "get_extraction_schema",
    "PARSING_SYSTEM_PROMPT",
    "CORRECTION_SYSTEM_PROMPT",
]
