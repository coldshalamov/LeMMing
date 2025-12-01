"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_base_path(tmp_path: Path) -> Path:
    """Create a temporary base path for testing."""
    return tmp_path


@pytest.fixture
def mock_org_chart() -> dict[str, Any]:
    """Mock organization chart."""
    return {
        "manager": {"send_to": ["planner", "hr"], "read_from": ["planner", "hr"]},
        "planner": {"send_to": ["manager"], "read_from": ["manager"]},
        "hr": {"send_to": ["manager"], "read_from": ["manager"]},
    }


@pytest.fixture
def mock_org_config() -> dict[str, Any]:
    """Mock organization configuration."""
    return {"base_turn_seconds": 10, "summary_every_n_turns": 12, "max_turns": None}


@pytest.fixture
def mock_credits() -> dict[str, Any]:
    """Mock credits configuration."""
    return {
        "manager": {"model": "gpt-4.1-mini", "cost_per_action": 0.01, "credits_left": 100.0},
        "planner": {"model": "gpt-4.1-mini", "cost_per_action": 0.01, "credits_left": 100.0},
        "hr": {"model": "gpt-4.1-mini", "cost_per_action": 0.01, "credits_left": 100.0},
    }


@pytest.fixture
def mock_models() -> dict[str, Any]:
    """Mock model registry."""
    return {
        "gpt-4.1": {"provider": "openai", "model_name": "gpt-4.1"},
        "gpt-4.1-mini": {"provider": "openai", "model_name": "gpt-4.1-mini"},
    }


@pytest.fixture
def setup_config_files(temp_base_path: Path, mock_org_chart, mock_org_config, mock_credits, mock_models):
    """Set up configuration files in temp directory."""
    config_dir = temp_base_path / "lemming" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    (config_dir / "org_chart.json").write_text(json.dumps(mock_org_chart, indent=2))
    (config_dir / "org_config.json").write_text(json.dumps(mock_org_config, indent=2))
    (config_dir / "credits.json").write_text(json.dumps(mock_credits, indent=2))
    (config_dir / "models.json").write_text(json.dumps(mock_models, indent=2))

    return config_dir


@pytest.fixture
def setup_agent_dirs(temp_base_path: Path):
    """Set up agent directories."""
    agents_dir = temp_base_path / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    for agent in ["manager", "planner", "hr"]:
        agent_dir = agents_dir / agent
        agent_dir.mkdir(exist_ok=True)
        for subdir in ["outbox", "memory", "logs", "config"]:
            (agent_dir / subdir).mkdir(exist_ok=True)

        # Create resume
        resume = f"""Name: {agent.upper()}
Role: Test role for {agent}
Description: Test agent {agent}

[INSTRUCTIONS]
Test instructions for {agent}.

[CONFIG]
{{
  "model": "gpt-4.1-mini",
  "org_speed_multiplier": 1,
  "send_to": [],
  "read_from": [],
  "max_credits": 100.0,
  "priority": "normal"
}}
"""
        (agent_dir / "resume.txt").write_text(resume)

    return agents_dir


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch("lemming.models.OpenAI") as mock_client:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"messages": [], "notes": "Test response"}'
        mock_client.return_value.chat.completions.create.return_value = mock_response
        yield mock_client


@pytest.fixture(autouse=True)
def reset_module_caches():
    """Reset module-level caches before each test."""
    from lemming import org

    org.reset_caches()
    yield
    org.reset_caches()
