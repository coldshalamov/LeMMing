from pathlib import Path

import pytest

from lemming.config_validation import (
    ValidationError,
    validate_credits,
    validate_everything,
    validate_models,
    validate_org_chart,
    validate_resume_file,
)


def test_validate_resume_file_success(tmp_path: Path):
    resume = tmp_path / "resume.txt"
    resume.write_text(
        """Name: TESTER
Role: Testing agent
Description: Ensures validation works

[INSTRUCTIONS]
Follow instructions.

[CONFIG]
{
  "model": "gpt-4.1-mini",
  "org_speed_multiplier": 1,
  "send_to": ["manager"],
  "read_from": ["manager"],
  "max_credits": 10.0
}
"""
    )

    parsed = validate_resume_file(resume)
    assert parsed["name"] == "TESTER"
    assert parsed["config_json"]["model"] == "gpt-4.1-mini"


def test_validate_resume_file_missing_section(tmp_path: Path):
    resume = tmp_path / "bad_resume.txt"
    resume.write_text("Name: TEST\nRole: Missing config\nDescription: none\n")

    with pytest.raises(ValidationError):
        validate_resume_file(resume)


def test_validate_org_chart_rejects_non_strings():
    with pytest.raises(ValidationError):
        validate_org_chart({"agent": {"send_to": [1], "read_from": ["x"]}})


def test_validate_models_rejects_wrong_shape():
    with pytest.raises(ValidationError):
        validate_models({"bad": {"provider": 123, "model_name": "gpt"}})


def test_validate_credits_rejects_missing_fields():
    with pytest.raises(ValidationError):
        validate_credits({"agent": {"model": "x"}})


def test_validate_everything_reports_missing_files(tmp_path: Path):
    errors = validate_everything(tmp_path)
    assert any("Missing required config file" in err for err in errors)
