"""Validation helpers for LeMMing configuration and resumes."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    """Raised when configuration validation fails."""


def _require_keys(mapping: dict[str, Any], required: Iterable[str], context: str) -> None:
    missing = [key for key in required if key not in mapping]
    if missing:
        raise ValidationError(f"Missing keys {missing} in {context}")


def _require_type(value: Any, expected_type: type | tuple[type, ...], context: str) -> None:
    if not isinstance(value, expected_type):
        type_names = (
            ", ".join(t.__name__ for t in expected_type)
            if isinstance(expected_type, tuple)
            else expected_type.__name__
        )
        raise ValidationError(f"Expected {context} to be {type_names}, got {type(value).__name__}")


def validate_resume_config(config: dict[str, Any], resume_path: Path | None = None) -> None:
    """Validate the CONFIG block inside a resume file."""

    context = f"resume config ({resume_path})" if resume_path else "resume config"
    _require_keys(config, ["model", "org_speed_multiplier", "send_to", "read_from", "max_credits"], context)

    _require_type(config.get("model"), str, f"model in {context}")
    _require_type(config.get("org_speed_multiplier"), (int, float), f"org_speed_multiplier in {context}")
    _require_type(config.get("send_to"), list, f"send_to in {context}")
    _require_type(config.get("read_from"), list, f"read_from in {context}")
    _require_type(config.get("max_credits"), (int, float), f"max_credits in {context}")

    for field in ("send_to", "read_from"):
        entries = config.get(field, [])
        if not all(isinstance(item, str) for item in entries):
            raise ValidationError(f"All entries in {field} must be strings in {context}")

    if config.get("org_speed_multiplier", 1) <= 0:
        raise ValidationError(f"org_speed_multiplier must be positive in {context}")

    if config.get("max_credits", 0) < 0:
        raise ValidationError(f"max_credits must be non-negative in {context}")


def validate_org_chart(chart: dict[str, Any]) -> None:
    """Ensure the org chart maps agents to send_to/read_from lists."""

    _require_type(chart, dict, "org_chart")
    for agent, entry in chart.items():
        _require_type(entry, dict, f"org_chart entry for {agent}")
        _require_keys(entry, ["send_to", "read_from"], f"org_chart entry for {agent}")
        _require_type(entry["send_to"], list, f"send_to for {agent}")
        _require_type(entry["read_from"], list, f"read_from for {agent}")
        for field in ("send_to", "read_from"):
            if not all(isinstance(item, str) for item in entry[field]):
                raise ValidationError(f"All entries in {field} for {agent} must be strings")


def validate_org_config(config: dict[str, Any]) -> None:
    """Ensure org_config contains expected numeric fields."""

    _require_type(config, dict, "org_config")
    _require_keys(config, ["base_turn_seconds", "summary_every_n_turns", "max_turns"], "org_config")
    _require_type(config["base_turn_seconds"], (int, float), "base_turn_seconds")
    _require_type(config["summary_every_n_turns"], (int, float), "summary_every_n_turns")
    if config["base_turn_seconds"] <= 0:
        raise ValidationError("base_turn_seconds must be positive")
    if config["summary_every_n_turns"] < 0:
        raise ValidationError("summary_every_n_turns must be non-negative")


def validate_credits(credits: dict[str, Any]) -> None:
    """Ensure credits.json entries contain the required numeric fields."""

    _require_type(credits, dict, "credits")
    for agent, entry in credits.items():
        _require_type(entry, dict, f"credits entry for {agent}")
        _require_keys(entry, ["model", "cost_per_action", "credits_left"], f"credits entry for {agent}")
        _require_type(entry["model"], str, f"model in credits entry for {agent}")
        _require_type(entry["cost_per_action"], (int, float), f"cost_per_action for {agent}")
        _require_type(entry["credits_left"], (int, float), f"credits_left for {agent}")


def validate_models(models: dict[str, Any]) -> None:
    """Ensure models.json entries contain provider/model_name fields."""

    _require_type(models, dict, "models")
    for key, entry in models.items():
        _require_type(entry, dict, f"models entry for {key}")
        _require_keys(entry, ["provider", "model_name"], f"models entry for {key}")
        _require_type(entry["provider"], str, f"provider in models entry for {key}")
        _require_type(entry["model_name"], str, f"model_name in models entry for {key}")
        if "provider_config" in entry and not isinstance(entry["provider_config"], dict):
            raise ValidationError(f"provider_config must be a dict in models entry for {key}")


def validate_resume_file(resume_path: Path) -> dict[str, Any]:
    """Parse and validate a resume file without creating an Agent."""

    content = resume_path.read_text(encoding="utf-8")
    if "[INSTRUCTIONS]" not in content or "[CONFIG]" not in content:
        raise ValidationError(f"Resume {resume_path} must contain [INSTRUCTIONS] and [CONFIG] sections")

    header_text, remainder = content.split("[INSTRUCTIONS]", 1)
    instructions_part, config_part = remainder.split("[CONFIG]", 1)

    header_lines = [line.strip() for line in header_text.strip().splitlines() if line.strip()]
    header_map: dict[str, str] = {}
    for line in header_lines:
        if ":" not in line:
            raise ValidationError(f"Malformed header line '{line}' in {resume_path}")
        key, value = line.split(":", 1)
        header_map[key.strip().lower()] = value.strip()

    for field in ("name", "role", "description"):
        if not header_map.get(field):
            raise ValidationError(f"Missing header '{field.title()}' in {resume_path}")

    instructions_text = instructions_part.strip()
    if not instructions_text:
        raise ValidationError(f"[INSTRUCTIONS] cannot be empty in {resume_path}")

    try:
        config_json = json.loads(config_part.strip())
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in [CONFIG] for {resume_path}: {exc}") from exc

    validate_resume_config(config_json, resume_path)

    return {
        "name": header_map["name"],
        "role": header_map["role"],
        "description": header_map["description"],
        "instructions_text": instructions_text,
        "config_json": config_json,
        "resume_text": content,
    }


def validate_everything(base_path: Path) -> list[str]:
    """Validate configs and resumes; return a list of error messages."""

    errors: list[str] = []
    config_dir = base_path / "lemming" / "config"

    def _load_json(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    file_validators = [
        (config_dir / "org_chart.json", validate_org_chart),
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
        for resume_path in agents_dir.glob("*/resume.txt"):
            try:
                validate_resume_file(resume_path)
            except Exception as exc:  # pragma: no cover - surfaced to caller
                errors.append(f"{resume_path}: {exc}")

    return errors
