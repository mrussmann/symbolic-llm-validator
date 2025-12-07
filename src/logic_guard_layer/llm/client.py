"""OpenRouter LLM client for Logic-Guard-Layer."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Exception for LLM-related errors."""
    pass


@dataclass
class OpenRouterConfig:
    """Configuration for OpenRouter API client."""
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "tngtech/deepseek-r1t2-chimera:free"
    timeout: float = 60.0
    max_retries: int = 3


class OpenRouterClient:
    """
    Async LLM client for OpenRouter API.
    Default model: tngtech/deepseek-r1t2-chimera:free
    """

    def __init__(self, config: OpenRouterConfig):
        """Initialize the OpenRouter client.

        Args:
            config: OpenRouter configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "HTTP-Referer": "https://logic-guard-layer.app",
                    "X-Title": "Logic-Guard-Layer",
                    "Content-Type": "application/json",
                }
            )
        return self._client

    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate completion using OpenRouter API.

        Args:
            prompt: The input prompt
            model: Model to use (defaults to tngtech/deepseek-r1t2-chimera:free)
            temperature: Sampling temperature (0 for deterministic)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt

        Returns:
            Generated text response

        Raises:
            LLMError: If the API call fails
        """
        client = await self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.config.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"OpenRouter API call attempt {attempt + 1}/{self.config.max_retries}")
                response = await client.post("/chat/completions", json=payload)
                response.raise_for_status()

                data = response.json()

                if "choices" not in data or len(data["choices"]) == 0:
                    raise LLMError("No choices in API response")

                content = data["choices"][0].get("message", {}).get("content", "")
                if not content:
                    raise LLMError("Empty content in API response")

                logger.debug(f"OpenRouter API call successful, response length: {len(content)}")
                return content

            except httpx.HTTPStatusError as e:
                last_error = e
                status_code = e.response.status_code

                if status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                    await asyncio.sleep(wait_time)
                    continue
                elif status_code == 401:
                    raise LLMError("Invalid API key") from e
                elif status_code == 400:
                    error_detail = e.response.text
                    raise LLMError(f"Bad request: {error_detail}") from e
                else:
                    logger.error(f"HTTP error: {status_code} - {e.response.text}")
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    raise LLMError(f"OpenRouter API error: {e}") from e

            except httpx.RequestError as e:
                last_error = e
                logger.error(f"Request error: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise LLMError(f"Request failed: {e}") from e

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error: {e}")
                raise LLMError(f"Unexpected error: {e}") from e

        raise LLMError(f"Max retries exceeded. Last error: {last_error}")

    async def complete_json(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> dict:
        """
        Generate JSON completion using OpenRouter API.

        Args:
            prompt: The input prompt (should request JSON output)
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Parsed JSON response

        Raises:
            LLMError: If the API call fails or JSON parsing fails
        """
        import json

        response = await self.complete(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info(f"Raw LLM response: {response[:500]}...")

        # Try to extract JSON from the response
        response = response.strip()

        # Handle markdown code blocks
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        try:
            parsed = json.loads(response)
            logger.info(f"Parsed JSON: {parsed}")
            return parsed
        except json.JSONDecodeError as e:
            # Try to find JSON in the response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                try:
                    parsed = json.loads(response[start_idx:end_idx])
                    logger.info(f"Parsed JSON (extracted): {parsed}")
                    return parsed
                except json.JSONDecodeError:
                    pass

            logger.error(f"Failed to parse JSON: {response}")
            raise LLMError(f"Failed to parse JSON response: {e}") from e

    async def close(self):
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


def create_client_from_settings() -> OpenRouterClient:
    """Create an OpenRouter client from application settings.

    Returns:
        Configured OpenRouterClient instance
    """
    from logic_guard_layer.config import settings

    config = OpenRouterConfig(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        default_model=settings.openrouter_model,
        timeout=settings.llm_timeout,
        max_retries=settings.llm_max_retries,
    )
    return OpenRouterClient(config)
