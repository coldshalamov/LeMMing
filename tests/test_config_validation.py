import json
from pathlib import Path

from lemming.config_validation import ValidationError, validate_everything, validate_resume_file


def _write_valid_config(base_path: Path) -> None:
    config_dir = base_path / "lemming" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "org_config.json").write_text(
        json.dumps(
            {
                "base_turn_seconds": 5,
                "summary_every_n_turns": 10,
                "max_turns": None,
                "max_outbox_age_ticks": 100,
            }
        ),
        encoding="utf-8",
    )
    (config_dir / "credits.json").write_text(
        json.dumps(
            {
                "alpha": {"model": "gpt-4.1-mini", "cost_per_action": 0.01, "credits_left": 5},
            }
        ),
        encoding="utf-8",
    )
    (config_dir / "models.json").write_text(
        json.dumps(
            {
                "gpt-4.1-mini": {
                    "provider": "openai",
                    "model_name": "gpt-4.1-mini",
                    "provider_config": {},
                }
            }
        ),
        encoding="utf-8",
    )


def _write_resume(base_path: Path, name: str) -> None:
    agent_dir = base_path / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    resume = {
        "name": name,
        "title": name.title(),
        "short_description": f"Agent {name}",
        "workflow_description": "",
        "instructions": "Follow the plan.",
        "model": {"key": "gpt-4.1-mini"},
        "permissions": {"read_outboxes": ["*"], "tools": []},
        "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},
        "credits": {"max_credits": 10, "soft_cap": 5},
    }
    (agent_dir / "resume.json").write_text(json.dumps(resume), encoding="utf-8")


def test_validate_everything_success(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    _write_resume(tmp_path, "alpha")

    errors = validate_everything(tmp_path)

    assert errors == []


def test_validate_everything_reports_schema_path(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    _write_resume(tmp_path, "alpha")

    # break the credits config
    credits_path = tmp_path / "lemming" / "config" / "credits.json"
    credits_data = {"alpha": {"model": "gpt-4.1-mini", "credits_left": 5}}
    credits_path.write_text(json.dumps(credits_data), encoding="utf-8")

    errors = validate_everything(tmp_path)

    assert len(errors) == 1
    assert "credits.json" in errors[0]
    assert "cost_per_action" in errors[0]


def test_validate_resume_uses_schema(tmp_path: Path) -> None:
    resume_path = tmp_path / "resume.json"
    resume_path.write_text(
        json.dumps({"name": "alpha", "title": "", "model": {}, "permissions": {}, "schedule": {}}), encoding="utf-8"
    )

    try:
        validate_resume_file(resume_path)
    except ValidationError as exc:
        message = str(exc)
    else:  # pragma: no cover - defensive guard
        raise AssertionError("validation should fail for incomplete resume")

    assert "resume.json" in message
    assert "short_description" in message
    assert "permissions -> read_outboxes" in message or "read_outboxes" in message
