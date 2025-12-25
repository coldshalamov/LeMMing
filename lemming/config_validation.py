"""Validation helpers for LeMMing configuration and resumes."""

from __future__ import annotations

import json
from collections.abc import Iterable
from importlib import resources
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft7Validator


class ValidationError(ValueError):
    """Raised when configuration validation fails."""


def validate_org_config(config: dict[str, Any]) -> None:
    _validate_against_schema(config, "org_config_schema.json", "org_config")


def validate_credits(credits: dict[str, Any]) -> None:
    _validate_against_schema(credits, "credits_schema.json", "credits")


def validate_models(models: dict[str, Any]) -> None:
    _validate_against_schema(models, "models_schema.json", "models")


def validate_resume_file(resume_path: Path) -> dict[str, Any]:
    try:
        raw_content = resume_path.read_text(encoding="utf-8")
        content = cast(dict[str, Any], json.loads(raw_content))
    except json.JSONDecodeError as exc:  # pragma: no cover - surfaced to caller
        raise ValidationError(f"Invalid JSON in {resume_path}: {exc}") from exc

    _validate_against_schema(content, "resume_schema.json", str(resume_path))

    return content


def _validate_against_schema(instance: Any, schema_name: str, context: str) -> None:
    errors = list(
        _format_jsonschema_error(error) for error in _iter_schema_errors(schema_name, instance)
    )
    if errors:
        raise ValidationError(f"{context}: " + "; ".join(errors))


def _iter_schema_errors(schema_name: str, instance: Any) -> Iterable[Any]:
    schema_path = resources.files(__package__).joinpath("schemas", schema_name)
    with resources.as_file(schema_path) as path:
        schema = json.loads(path.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    return validator.iter_errors(instance)


def _format_jsonschema_error(error: Any) -> str:
    path = " -> ".join(str(p) for p in error.absolute_path) or "<root>"
    return f"{path}: {error.message}"


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
