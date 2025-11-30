"""Tests for models module."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from lemming.models import ModelConfig, ModelRegistry, call_llm


def test_model_config():
    """Test ModelConfig dataclass."""
    config = ModelConfig(provider="openai", model_name="gpt-4.1")
    assert config.provider == "openai"
    assert config.model_name == "gpt-4.1"


def test_model_registry_load(temp_base_path, setup_config_files):
    """Test loading model registry."""
    registry = ModelRegistry(config_dir=temp_base_path / "lemming" / "config")
    config = registry.get("gpt-4.1")

    assert config.provider == "openai"
    assert config.model_name == "gpt-4.1"


def test_model_registry_get_mini(temp_base_path, setup_config_files):
    """Test getting mini model."""
    registry = ModelRegistry(config_dir=temp_base_path / "lemming" / "config")
    config = registry.get("gpt-4.1-mini")

    assert config.provider == "openai"
    assert config.model_name == "gpt-4.1-mini"


def test_model_registry_missing_key(temp_base_path, setup_config_files):
    """Test getting nonexistent model key."""
    registry = ModelRegistry(config_dir=temp_base_path / "lemming" / "config")

    with pytest.raises(KeyError, match="not found in registry"):
        registry.get("nonexistent-model")


def test_model_registry_missing_file(temp_base_path):
    """Test loading when models.json doesn't exist."""
    registry = ModelRegistry(config_dir=temp_base_path / "lemming" / "config")

    with pytest.raises(FileNotFoundError, match="Model registry not found"):
        registry.get("gpt-4.1")


def test_model_registry_lazy_loading(temp_base_path, setup_config_files):
    """Test that registry loads lazily."""
    registry = ModelRegistry(config_dir=temp_base_path / "lemming" / "config")
    assert registry._loaded is False

    registry.get("gpt-4.1")
    assert registry._loaded is True


def test_model_registry_caching(temp_base_path, setup_config_files):
    """Test that registry caches loaded models."""
    registry = ModelRegistry(config_dir=temp_base_path / "lemming" / "config")

    config1 = registry.get("gpt-4.1")
    config2 = registry.get("gpt-4.1")

    assert config1 is config2  # Same object


@patch("openai.OpenAI")
def test_call_llm_success(mock_openai, temp_base_path, setup_config_files):
    """Test successful LLM call."""
    # Setup mock
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    # Call LLM
    messages = [{"role": "user", "content": "Hello"}]
    response = call_llm("gpt-4.1-mini", messages, config_dir=temp_base_path / "lemming" / "config")

    assert response == "Test response"
    mock_client.chat.completions.create.assert_called_once()


@patch("openai.OpenAI")
def test_call_llm_with_temperature(mock_openai, temp_base_path, setup_config_files):
    """Test LLM call with custom temperature."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response"
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    messages = [{"role": "user", "content": "Hello"}]
    call_llm("gpt-4.1-mini", messages, temperature=0.7, config_dir=temp_base_path / "lemming" / "config")

    call_args = mock_client.chat.completions.create.call_args
    assert call_args.kwargs["temperature"] == 0.7


@patch("openai.OpenAI")
def test_call_llm_empty_response(mock_openai, temp_base_path, setup_config_files):
    """Test LLM call with None content."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    messages = [{"role": "user", "content": "Hello"}]
    response = call_llm("gpt-4.1-mini", messages, config_dir=temp_base_path / "lemming" / "config")

    assert response == ""


def test_call_llm_unsupported_provider(temp_base_path):
    """Test error when using unsupported provider."""
    # Create models.json with unsupported provider
    config_dir = temp_base_path / "lemming" / "config"
    config_dir.mkdir(parents=True)

    models = {"custom-model": {"provider": "unsupported", "model_name": "test"}}
    (config_dir / "models.json").write_text(json.dumps(models))

    messages = [{"role": "user", "content": "Hello"}]

    with pytest.raises(ValueError, match="Unknown provider"):
        call_llm("custom-model", messages, config_dir=config_dir)


@patch("openai.OpenAI")
def test_call_llm_multiple_messages(mock_openai, temp_base_path, setup_config_files):
    """Test LLM call with multiple messages."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response"
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    messages = [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "user", "content": "How are you?"},
    ]

    call_llm("gpt-4.1", messages, config_dir=temp_base_path / "lemming" / "config")

    call_args = mock_client.chat.completions.create.call_args
    assert len(call_args.kwargs["messages"]) == 4
