from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from .config_validation import validate_models
from .providers import get_provider

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    provider: str
    model_name: str
    provider_config: dict | None = None


class ModelRegistry:
    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or Path(__file__).parent / "config"
        self._models: dict[str, ModelConfig] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        models_path = self.config_dir / "models.json"
        if not models_path.exists():
            raise FileNotFoundError(f"Model registry not found at {models_path}")
        with models_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        validate_models(data)
        for key, cfg in data.items():
            self._models[key] = ModelConfig(
                provider=cfg["provider"],
                model_name=cfg["model_name"],
                provider_config=cfg.get("provider_config"),
            )
        self._loaded = True
        logger.debug(
            "models_loaded",
            extra={"event": "models_loaded", "path": str(models_path)},
        )

    def get(self, model_key: str) -> ModelConfig:
        self._load()
        if model_key not in self._models:
            raise KeyError(f"Model key '{model_key}' not found in registry")
        return self._models[model_key]


def call_llm(model_key: str, messages: list[dict], temperature: float = 0.2, config_dir: Path | None = None) -> str:
    """
    Call an LLM using the configured provider.

    Args:
        model_key: Key from models.json
        messages: List of message dicts
        temperature: Sampling temperature
        config_dir: Config directory path

    Returns:
        LLM response as string
    """
    registry = ModelRegistry(config_dir)
    config = registry.get(model_key)

    # Get provider instance
    provider_kwargs = config.provider_config or {}
    provider = get_provider(config.provider, **provider_kwargs)

    # Call the provider
    return provider.call(config.model_name, messages, temperature)
