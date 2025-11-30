"""Abstract LLM provider interface and implementations."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

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
        logger.info("Calling OpenAI model %s with %d messages", model_name, len(messages))

        response = self.client.chat.completions.create(
            model=model_name, messages=messages, temperature=temperature, **kwargs
        )

        content = response.choices[0].message.content
        logger.debug("OpenAI response content length: %s", len(content) if content else 0)
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
        logger.info("Calling Anthropic model %s with %d messages", model_name, len(messages))

        # Anthropic requires system messages to be separate
        system_messages = [m["content"] for m in messages if m["role"] == "system"]
        other_messages = [m for m in messages if m["role"] != "system"]

        # Combine system messages
        system = "\n\n".join(system_messages) if system_messages else None

        response = self.client.messages.create(
            model=model_name,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=temperature,
            system=system,
            messages=other_messages,
        )

        content = response.content[0].text if response.content else ""
        logger.debug("Anthropic response content length: %s", len(content))
        return content


class OllamaProvider(LLMProvider):
    """Ollama local model provider implementation."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def call(self, model_name: str, messages: list[dict[str, str]], temperature: float = 0.2, **kwargs: Any) -> str:
        """Call Ollama API."""
        import requests

        logger.info("Calling Ollama model %s with %d messages", model_name, len(messages))

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={"model": model_name, "messages": messages, "temperature": temperature, "stream": False},
                timeout=120,
            )
            response.raise_for_status()

            data = response.json()
            content = data.get("message", {}).get("content", "")
            logger.debug("Ollama response content length: %s", len(content))
            return content

        except Exception as exc:
            logger.error("Ollama API call failed: %s", exc)
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
    logger.info("Registered custom provider: %s", name)
