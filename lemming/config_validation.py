"""Validation helpers for LeMMing configuration and resumes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast


class ValidationError(ValueError):
    """Raised when configuration validation fails."""


def _require_keys(mapping: dict[str, Any], required: list[str], context: str) -> None:
    missing = [key for key in required if key not in mapping]
    if missing:
        raise ValidationError(f"Missing keys {missing} in {context}")


def _require_type(value: Any, expected_type: type | tuple[type, ...], context: str) -> None:
    if not isinstance(value, expected_type):
        names = (
            ", ".join(t.__name__ for t in expected_type)
            if isinstance(expected_type, tuple)
            else expected_type.__name__
        )
        raise ValidationError(f"Expected {context} to be {names}, got {type(value).__name__}")


def validate_org_config(config: dict[str, Any]) -> None:
    _require_keys(config, ["base_turn_seconds", "max_turns"], "org_config")
    _require_type(config["base_turn_seconds"], (int, float), "base_turn_seconds")
    if config["base_turn_seconds"] <= 0:
        raise ValidationError("base_turn_seconds must be positive")
    if config.get("max_turns") is not None and not isinstance(config.get("max_turns"), int):
        raise ValidationError("max_turns must be integer or null")


def validate_credits(credits: dict[str, Any]) -> None:
    _require_type(credits, dict, "credits")
    for agent, entry in credits.items():
        _require_type(entry, dict, f"credits entry for {agent}")
        _require_keys(entry, ["model", "cost_per_action", "credits_left"], f"credits entry for {agent}")
        _require_type(entry["model"], str, f"model for {agent}")
        _require_type(entry["cost_per_action"], (int, float), f"cost_per_action for {agent}")
        _require_type(entry["credits_left"], (int, float), f"credits_left for {agent}")


def validate_models(models: dict[str, Any]) -> None:
    _require_type(models, dict, "models")
    for key, entry in models.items():
        _require_type(entry, dict, f"models entry for {key}")
        _require_keys(entry, ["provider", "model_name"], f"models entry for {key}")
        _require_type(entry["provider"], str, f"provider for {key}")
        _require_type(entry["model_name"], str, f"model_name for {key}")
        if "provider_config" in entry and not isinstance(entry["provider_config"], dict):
            raise ValidationError(f"provider_config must be dict for {key}")


def validate_resume_file(resume_path: Path) -> dict[str, Any]:
    try:
        raw_content = resume_path.read_text(encoding="utf-8")
        content = cast(dict[str, Any], json.loads(raw_content))
    except json.JSONDecodeError as exc:  # pragma: no cover - surfaced to caller
        raise ValidationError(f"Invalid JSON in {resume_path}: {exc}") from exc

    _require_keys(
        content,
        ["name", "title", "short_description", "model", "permissions", "instructions"],
        str(resume_path),
    )
    if content.get("name") != resume_path.parent.name:
        raise ValidationError(
            f"Agent name {content.get('name')} does not match directory {resume_path.parent.name}"
        )

    _require_keys(content.get("model", {}), ["key"], f"model in {resume_path}")
    permissions = content.get("permissions", {})
    _require_keys(permissions, ["read_outboxes", "tools"], f"permissions in {resume_path}")
    if not isinstance(permissions.get("read_outboxes"), list) or not all(
        isinstance(x, str) for x in permissions.get("read_outboxes", [])
    ):
        raise ValidationError("permissions.read_outboxes must be list of strings")
    if not isinstance(permissions.get("tools"), list) or not all(
        isinstance(x, str) for x in permissions.get("tools", [])
    ):
        raise ValidationError("permissions.tools must be list of strings")

    return content


def validate_everything(base_path: Path) -> list[str]:
    errors: list[str] = []
    config_dir = base_path / "lemming" / "config"

    def _load_json(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            loaded: dict[str, Any] = json.load(f)
        return loaded

    file_validators = [
        (config_dir / "org_config.json", validate_org_config),
        (config_dir / "credits.json", validate_credits),
        (config_dir / "models.json", validate_models),
    ]

    for path, validator in file_validators:
        try:
            data = _load_json(path)
            validator(data)
        except FileNotFoundError:
            errors.append(f"Missing required config file: {path}")
        except Exception as exc:  # pragma: no cover - surfaced to caller
            errors.append(f"{path.name}: {exc}")

    agents_dir = base_path / "agents"
    if agents_dir.exists():
        for resume_path in agents_dir.glob("*/resume.json"):
            try:
                validate_resume_file(resume_path)
            except Exception as exc:  # pragma: no cover - surfaced to caller
                errors.append(f"{resume_path}: {exc}")

    return errors
