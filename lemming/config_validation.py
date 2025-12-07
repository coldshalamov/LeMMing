"""Validation helpers for LeMMing configuration and resumes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    """Raised when configuration validation fails."""


def _require_keys(mapping: dict[str, Any], required: list[str], context: str) -> None:
    missing = [key for key in required if key not in mapping]
    if missing:
        raise ValidationError(f"Missing keys {missing} in {context}")


def _require_type(value: Any, expected_type: type | tuple[type, ...], context: str) -> None:
    if not isinstance(value, expected_type):
        names = (
            ", ".join(t.__name__ for t in expected_type) if isinstance(expected_type, tuple) else expected_type.__name__
        )
        raise ValidationError(f"Expected {context} to be {names}, got {type(value).__name__}")


def validate_org_config(config: dict[str, Any]) -> None:
    """
    Validate organization configuration.

    Args:
        config: Organization configuration dictionary

    Raises:
        ValidationError: If validation fails
    """
    _require_keys(config, ["base_turn_seconds", "max_turns"], "org_config")
    _require_type(config["base_turn_seconds"], (int, float), "base_turn_seconds")
    if config["base_turn_seconds"] <= 0:
        raise ValidationError("base_turn_seconds must be positive")
    if config.get("max_turns") is not None and not isinstance(config.get("max_turns"), int):
        raise ValidationError("max_turns must be integer or null")


def validate_credits(credits: dict[str, Any]) -> None:
    """
    Validate credits configuration.

    Args:
        credits: Credits configuration dictionary

    Raises:
        ValidationError: If validation fails
    """
    _require_type(credits, dict, "credits")
    for agent, entry in credits.items():
        _require_type(entry, dict, f"credits entry for {agent}")
        _require_keys(entry, ["model", "cost_per_action", "credits_left"], f"credits entry for {agent}")
        _require_type(entry["model"], str, f"model for {agent}")
        _require_type(entry["cost_per_action"], (int, float), f"cost_per_action for {agent}")
        _require_type(entry["credits_left"], (int, float), f"credits_left for {agent}")

        # Additional validation for sensible values
        if entry["cost_per_action"] < 0:
            raise ValidationError(f"cost_per_action for {agent} must be non-negative")
        if entry["credits_left"] < 0:
            raise ValidationError(f"credits_left for {agent} must be non-negative")


def validate_models(models: dict[str, Any]) -> None:
    """
    Validate models configuration.

    Args:
        models: Models configuration dictionary

    Raises:
        ValidationError: If validation fails
    """
    _require_type(models, dict, "models")
    valid_providers = ["openai", "anthropic", "ollama"]  # Known providers

    for key, entry in models.items():
        _require_type(entry, dict, f"models entry for {key}")
        _require_keys(entry, ["provider", "model_name"], f"models entry for {key}")
        _require_type(entry["provider"], str, f"provider for {key}")
        _require_type(entry["model_name"], str, f"model_name for {key}")

        # Warn about unknown providers (but don't fail)
        if entry["provider"] not in valid_providers:
            import logging

            logging.warning(
                f"Unknown provider '{entry['provider']}' for model '{key}'. " f"Known providers: {valid_providers}"
            )

        if "provider_config" in entry and not isinstance(entry["provider_config"], dict):
            raise ValidationError(f"provider_config must be dict for {key}")


def validate_resume_file(resume_path: Path) -> dict[str, Any]:
    """
    Validate a resume.json file.

    Args:
        resume_path: Path to the resume.json file

    Returns:
        The validated resume content

    Raises:
        ValidationError: If validation fails
    """
    try:
        content = json.loads(resume_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - surfaced to caller
        raise ValidationError(f"Invalid JSON in {resume_path}: {exc}") from exc
    except FileNotFoundError as exc:
        raise ValidationError(f"Resume file not found: {resume_path}") from exc

    _require_keys(
        content,
        ["name", "title", "short_description", "model", "permissions", "instructions"],
        str(resume_path),
    )

    # Validate agent name matches directory
    if content.get("name") != resume_path.parent.name:
        raise ValidationError(
            f"Agent name '{content.get('name')}' does not match directory '{resume_path.parent.name}'. "
            f"These must match for proper agent loading."
        )

    # Validate model configuration
    _require_keys(content.get("model", {}), ["key"], f"model in {resume_path}")
    _require_type(content["model"]["key"], str, f"model.key in {resume_path}")

    # Validate permissions
    permissions = content.get("permissions", {})
    _require_keys(permissions, ["read_outboxes", "tools"], f"permissions in {resume_path}")

    if not isinstance(permissions.get("read_outboxes"), list):
        raise ValidationError(f"permissions.read_outboxes must be a list in {resume_path}")
    if not all(isinstance(x, str) for x in permissions.get("read_outboxes", [])):
        raise ValidationError(f"permissions.read_outboxes must contain only strings in {resume_path}")

    if not isinstance(permissions.get("tools"), list):
        raise ValidationError(f"permissions.tools must be a list in {resume_path}")
    if not all(isinstance(x, str) for x in permissions.get("tools", [])):
        raise ValidationError(f"permissions.tools must contain only strings in {resume_path}")

    # Validate schedule if present
    if "schedule" in content:
        schedule = content["schedule"]
        if "run_every_n_ticks" in schedule:
            _require_type(schedule["run_every_n_ticks"], int, f"schedule.run_every_n_ticks in {resume_path}")
            if schedule["run_every_n_ticks"] < 1:
                raise ValidationError(f"schedule.run_every_n_ticks must be at least 1 in {resume_path}")
        if "phase_offset" in schedule:
            _require_type(schedule["phase_offset"], int, f"schedule.phase_offset in {resume_path}")
            if schedule["phase_offset"] < 0:
                raise ValidationError(f"schedule.phase_offset must be non-negative in {resume_path}")

    # Validate instructions is not empty
    if not content.get("instructions") or not content["instructions"].strip():
        raise ValidationError(f"instructions cannot be empty in {resume_path}")

    return content


def validate_everything(base_path: Path) -> list[str]:
    """
    Validate all configuration files and agent resumes.

    Args:
        base_path: Base path of the LeMMing installation

    Returns:
        List of error messages (empty if all valid)
    """
    errors: list[str] = []
    config_dir = base_path / "lemming" / "config"

    def _load_json(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    file_validators = [
        (config_dir / "org_config.json", validate_org_config, "Organization Config"),
        (config_dir / "credits.json", validate_credits, "Credits Config"),
        (config_dir / "models.json", validate_models, "Models Config"),
    ]

    for path, validator, name in file_validators:
        try:
            data = _load_json(path)
            validator(data)
        except FileNotFoundError:
            errors.append(f"[{name}] Missing required config file: {path}")
        except json.JSONDecodeError as exc:
            errors.append(f"[{name}] Invalid JSON in {path}: {exc}")
        except ValidationError as exc:
            errors.append(f"[{name}] {exc}")
        except Exception as exc:  # pragma: no cover - unexpected errors
            errors.append(f"[{name}] Unexpected error validating {path}: {exc}")

    agents_dir = base_path / "agents"
    if agents_dir.exists():
        resume_paths = sorted(agents_dir.glob("*/resume.json"))
        # Empty organizations are allowed, just validate any resumes that exist
        for resume_path in resume_paths:
            try:
                validate_resume_file(resume_path)
            except ValidationError as exc:
                errors.append(f"[Agent {resume_path.parent.name}] {exc}")
            except Exception as exc:  # pragma: no cover - unexpected errors
                errors.append(f"[Agent {resume_path.parent.name}] Unexpected error: {exc}")
    else:
        errors.append("[Agents] agents/ directory not found")

    return errors
