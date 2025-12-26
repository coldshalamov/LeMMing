"""Abstract LLM provider interface and implementations."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar, cast

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def call(self, model_name: str, messages: list[dict[str, str]], temperature: float = 0.2, **kwargs: Any) -> str:
        """
        Call the LLM with the given messages.

        Args:
            model_name: Name/ID of the model to use
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Returns:
            The LLM's response as a string
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""

    def __init__(self):
        try:
            from openai import OpenAI

            self.client = OpenAI()
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")

    def call(self, model_name: str, messages: list[dict[str, str]], temperature: float = 0.2, **kwargs: Any) -> str:
        """Call OpenAI API."""
        logger.info(
            "openai_call",
            extra={
                "event": "openai_call",
                "model_name": model_name,
                "message_count": len(messages),
            },
        )

        response = self.client.chat.completions.create(
            model=model_name,
            messages=cast(Any, messages),
            temperature=temperature,
            **kwargs,
        )

        content = response.choices[0].message.content
        logger.debug(
            "openai_response",
            extra={
                "event": "openai_response",
                "model_name": model_name,
                "content_length": len(content) if content else 0,
            },
        )
        return content or ""


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation."""

    def __init__(self):
        try:
            from anthropic import Anthropic

            self.client = Anthropic()
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with: pip install -e '.[llm]'")

    def call(self, model_name: str, messages: list[dict[str, str]], temperature: float = 0.2, **kwargs: Any) -> str:
        """Call Anthropic Claude API."""
        logger.info(
            "anthropic_call",
            extra={
                "event": "anthropic_call",
                "model_name": model_name,
                "message_count": len(messages),
            },
        )

        # Anthropic requires system messages to be separate
        system_messages = [m["content"] for m in messages if m["role"] == "system"]
        other_messages = [m for m in messages if m["role"] != "system"]

        # Combine system messages
        system = "\n\n".join(system_messages) if system_messages else None

        response = self.client.messages.create(
            model=model_name,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=temperature,
            system=cast(Any, system),
            messages=cast(Any, other_messages),
        )

        content_blocks = cast(list[Any], response.content or [])
        text_block = next((block for block in content_blocks if getattr(block, "text", None)), None)
        content = cast(str, getattr(text_block, "text", "")) if text_block else ""
        logger.debug(
            "anthropic_response",
            extra={
                "event": "anthropic_response",
                "model_name": model_name,
                "content_length": len(content),
            },
        )
        return content


class OllamaProvider(LLMProvider):
    """Ollama local model provider implementation."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def call(self, model_name: str, messages: list[dict[str, str]], temperature: float = 0.2, **kwargs: Any) -> str:
        """Call Ollama API."""
        import requests  # type: ignore[import-untyped]

        logger.info(
            "ollama_call",
            extra={
                "event": "ollama_call",
                "model_name": model_name,
                "message_count": len(messages),
            },
        )

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={"model": model_name, "messages": messages, "temperature": temperature, "stream": False},
                timeout=120,
            )
            response.raise_for_status()

            data = response.json()
            content = str(data.get("message", {}).get("content", ""))
            logger.debug(
                "ollama_response",
                extra={
                    "event": "ollama_response",
                    "model_name": model_name,
                    "content_length": len(content),
                },
            )
            return content

        except Exception as exc:
            logger.error(
                "ollama_call_failed",
                extra={
                    "event": "ollama_call_failed",
                    "model_name": model_name,
                    "error": str(exc),
                },
            )
            return f"Error calling Ollama: {exc}"


# Provider registry
_PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}


def get_provider(provider_name: str, **kwargs: Any) -> LLMProvider:
    """
    Get a provider instance by name.

    Args:
        provider_name: Name of the provider (openai, anthropic, ollama)
        **kwargs: Provider-specific initialization arguments

    Returns:
        Provider instance

    Raises:
        ValueError: If provider name is not recognized
    """
    provider_class = _PROVIDERS.get(provider_name.lower())

    if provider_class is None:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(_PROVIDERS.keys())}")

    return provider_class(**kwargs)


def register_provider(name: str, provider_class: type[LLMProvider]) -> None:
    """
    Register a custom provider.

    Args:
        name: Name to register the provider under
        provider_class: Provider class (must inherit from LLMProvider)
    """
    if not issubclass(provider_class, LLMProvider):
        raise TypeError("Provider class must inherit from LLMProvider")

    _PROVIDERS[name.lower()] = provider_class
    logger.info(
        "provider_registered",
        extra={"event": "provider_registered", "provider": name},
    )


T = TypeVar("T")


class CircuitBreaker:
    """Circuit breaker for LLM providers to prevent cascading failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing if service has recovered
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        """
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute a function with circuit breaker protection."""
        if self.state == "OPEN":
            # Check if we should attempt recovery
            if self.last_failure_time and time.time() - self.last_failure_time >= self.recovery_timeout:
                logger.info(
                    "circuit_half_open",
                    extra={"event": "circuit_half_open", "state": self.state},
                )
                self.state = "HALF_OPEN"
            else:
                raise RuntimeError("Circuit breaker is OPEN - too many recent failures")

        try:
            result = func(*args, **kwargs)
            # Success - reset failure count
            if self.state == "HALF_OPEN":
                logger.info(
                    "circuit_closed",
                    extra={"event": "circuit_closed", "state": "CLOSED"},
                )
                self.state = "CLOSED"
                self.failure_count = 0

            return result

        except Exception as exc:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                logger.error(
                    "circuit_opened",
                    extra={
                        "event": "circuit_opened",
                        "failures": self.failure_count,
                        "error": str(exc),
                    },
                )
                self.state = "OPEN"
            elif self.state == "HALF_OPEN":
                # Failed during recovery attempt
                logger.warning(
                    "circuit_recovery_failed",
                    extra={"event": "circuit_recovery_failed", "state": "OPEN"},
                )
                self.state = "OPEN"

            raise


class RetryingLLMProvider(LLMProvider):
    """Wrapper provider that adds retry logic and circuit breaker.

    Implements exponential backoff: 1s, 2s, 4s, 8s
    """

    def __init__(
        self,
        inner_provider: LLMProvider,
        max_retries: int = 3,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        """
        Args:
            inner_provider: The actual LLM provider to wrap
            max_retries: Maximum number of retry attempts
            circuit_breaker: Optional circuit breaker instance
        """
        self.inner_provider = inner_provider
        self.max_retries = max_retries
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

    def call(self, model_name: str, messages: list[dict[str, str]], temperature: float = 0.2, **kwargs: Any) -> str:
        """Call the inner provider with retry logic and circuit breaker."""
        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                # Call through circuit breaker
                return self.circuit_breaker.call(self.inner_provider.call, model_name, messages, temperature, **kwargs)

            except Exception as exc:
                last_exception = exc
                if attempt < self.max_retries:
                    # Exponential backoff: 1s, 2s, 4s, 8s
                    backoff = 2**attempt
                    logger.warning(
                        "llm_retrying",
                        extra={
                            "event": "llm_retrying",
                            "attempt": attempt + 1,
                            "max_attempts": self.max_retries + 1,
                            "backoff_seconds": backoff,
                            "error": str(exc),
                        },
                    )
                    time.sleep(backoff)
                else:
                    logger.error(
                        "llm_failed",
                        extra={
                            "event": "llm_failed",
                            "max_attempts": self.max_retries + 1,
                            "error": str(exc),
                        },
                    )

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise RuntimeError("LLM call failed with unknown error")
