"""Tests for configuration validation."""

from __future__ import annotations

import json
from pathlib import Path

from lemming.config_validation import (
    validate_credits,
    validate_everything,
    validate_models,
    validate_org_config,
)


def test_validate_org_config_valid() -> None:
    """Test validation of valid org config."""

    config = {"base_turn_seconds": 5, "max_turns": 100}
    # Should not raise
    validate_org_config(config)


def test_validate_org_config_missing_fields() -> None:
    """Test validation of org config with missing fields."""
    from lemming.config_validation import ValidationError

    config = {"base_turn_seconds": 5}  # missing max_turns
    try:
        validate_org_config(config)
        assert False, "Expected ValidationError"
    except ValidationError as e:
        assert "max_turns" in str(e)


def test_validate_org_config_invalid_type() -> None:
    """Test validation of org config with invalid type."""
    from lemming.config_validation import ValidationError

    config = {"base_turn_seconds": "5", "max_turns": 100}
    try:
        validate_org_config(config)
        assert False, "Expected ValidationError"
    except ValidationError as e:
        assert "base_turn_seconds" in str(e)


def test_validate_models_config_valid() -> None:
    """Test validation of valid models config."""
    config = {"gpt-4": {"provider": "openai", "model_name": "gpt-4"}}
    # Should not raise
    validate_models(config)


def test_validate_models_config_missing_fields() -> None:
    """Test validation of models config with missing fields."""
    from lemming.config_validation import ValidationError

    config = {"gpt-4": {"provider": "openai"}}  # missing model_name
    try:
        validate_models(config)
        assert False, "Expected ValidationError"
    except ValidationError as e:
        assert "model_name" in str(e)


def test_validate_credits_config_valid() -> None:
    """Test validation of valid credits config."""
    config = {
        "agent_a": {
            "model": "gpt-4",
            "cost_per_action": 0.01,
            "credits_left": 100.0,
        }
    }
    # Should not raise
    validate_credits(config)


def test_validate_credits_config_missing_fields() -> None:
    """Test validation of credits config with missing fields."""
    from lemming.config_validation import ValidationError

    config = {"agent_a": {"model": "gpt-4"}}  # missing cost_per_action and credits_left
    try:
        validate_credits(config)
        assert False, "Expected ValidationError"
    except ValidationError as e:
        assert "cost_per_action" in str(e) or "credits_left" in str(e)


def test_validate_everything_empty_org(tmp_path: Path) -> None:
    """Test validation of complete organization with no agents."""
    config_dir = tmp_path / "lemming" / "config"
    config_dir.mkdir(parents=True)
    (tmp_path / "agents").mkdir()

    (config_dir / "org_config.json").write_text(
        json.dumps({"base_turn_seconds": 1, "max_turns": None}),
        encoding="utf-8",
    )
    (config_dir / "models.json").write_text(
        json.dumps({"gpt-4": {"provider": "openai", "model_name": "gpt-4"}}),
        encoding="utf-8",
    )
    (config_dir / "credits.json").write_text(json.dumps({}), encoding="utf-8")

    errors = validate_everything(tmp_path)
    assert not errors


def test_validate_everything_with_agents(tmp_path: Path) -> None:
    """Test validation with agents and complete config."""
    config_dir = tmp_path / "lemming" / "config"
    config_dir.mkdir(parents=True)

    (config_dir / "org_config.json").write_text(
        json.dumps({"base_turn_seconds": 1, "max_turns": None}),
        encoding="utf-8",
    )
    (config_dir / "models.json").write_text(
        json.dumps({"test-model": {"provider": "openai", "model_name": "gpt-4.1-mini"}}),
        encoding="utf-8",
    )
    (config_dir / "credits.json").write_text(
        json.dumps(
            {
                "agent_a": {
                    "model": "test-model",
                    "cost_per_action": 0.01,
                    "credits_left": 10.0,
                }
            }
        ),
        encoding="utf-8",
    )

    agent_dir = tmp_path / "agents" / "agent_a"
    agent_dir.mkdir(parents=True)
    resume = {
        "name": "agent_a",
        "title": "Test Agent",
        "short_description": "A test agent",
        "model": {"key": "test-model"},
        "permissions": {"read_outboxes": [], "tools": []},
        "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},
        "instructions": "Test instructions",
    }
    (agent_dir / "resume.json").write_text(json.dumps(resume), encoding="utf-8")

    errors = validate_everything(tmp_path)
    assert not errors


def test_validate_everything_detects_multiple_errors(tmp_path: Path) -> None:
    """Test that validation catches errors across multiple configs."""
    config_dir = tmp_path / "lemming" / "config"
    config_dir.mkdir(parents=True)

    # Invalid org config
    (config_dir / "org_config.json").write_text(json.dumps({}), encoding="utf-8")

    # Invalid models config
    (config_dir / "models.json").write_text(
        json.dumps({"bad-model": {}}),
        encoding="utf-8",
    )

    # Invalid credits config
    (config_dir / "credits.json").write_text(json.dumps({"agent": {}}), encoding="utf-8")

    errors = validate_everything(tmp_path)
    assert len(errors) >= 3  # Should have errors from all configs
