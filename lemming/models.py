from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    provider: str
    model_name: str


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
        for key, cfg in data.items():
            self._models[key] = ModelConfig(provider=cfg["provider"], model_name=cfg["model_name"])
        self._loaded = True
        logger.debug("Loaded model registry from %s", models_path)

    def get(self, model_key: str) -> ModelConfig:
        self._load()
        if model_key not in self._models:
            raise KeyError(f"Model key '{model_key}' not found in registry")
        return self._models[model_key]


def call_llm(model_key: str, messages: list[dict], temperature: float = 0.2, config_dir: Path | None = None) -> str:
    registry = ModelRegistry(config_dir)
    config = registry.get(model_key)
    if config.provider != "openai":
        raise ValueError(f"Unsupported provider: {config.provider}")

    client = OpenAI()
    logger.info("Calling LLM model %s with %d messages", config.model_name, len(messages))
    response = client.chat.completions.create(
        model=config.model_name,
        messages=messages,
        temperature=temperature,
    )
    content = response.choices[0].message.content
    logger.debug("LLM response content length: %s", len(content) if content else 0)
    return content or ""
