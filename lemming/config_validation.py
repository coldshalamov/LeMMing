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
        ["name", "title", "model", "permissions", "schedule", "instructions"],
        str(resume_path),
    )
    if not content.get("short_description") and not content.get("description"):
        raise ValidationError("Missing short_description or description")

    model = content.get("model")
    if isinstance(model, dict):
        _require_keys(model, ["key"], f"model in {resume_path}")
    elif not isinstance(model, str):
        raise ValidationError("model must be a string key or object with 'key'")

    permissions = content.get("permissions", {}) or {}
    _require_keys(permissions, ["read_outboxes", "tools"], f"permissions in {resume_path}")
    for key in ["read_outboxes", "tools", "send_outboxes"]:
        if key in permissions and not isinstance(permissions.get(key, []), list):
            raise ValidationError(f"permissions.{key} must be list when provided")
    file_access = permissions.get("file_access")
    if file_access is not None:
        if not isinstance(file_access, dict):
            raise ValidationError("permissions.file_access must be a dict when provided")
        for sub in ["allow_read", "allow_write"]:
            if sub in file_access and not isinstance(file_access.get(sub, []), list):
                raise ValidationError(f"permissions.file_access.{sub} must be list")

    schedule = content.get("schedule", {}) or {}
    _require_keys(schedule, ["run_every_n_ticks", "phase_offset"], f"schedule in {resume_path}")
    if int(schedule.get("run_every_n_ticks", 0)) <= 0:
        raise ValidationError("schedule.run_every_n_ticks must be > 0")

    credits = content.get("credits")
    if credits is not None:
        if not isinstance(credits, dict):
            raise ValidationError("credits must be a dict when provided")
        for field in ["max_credits", "soft_cap"]:
            if field not in credits:
                raise ValidationError(f"Missing credits.{field}")

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
