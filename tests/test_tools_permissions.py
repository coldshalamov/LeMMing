from __future__ import annotations

from pathlib import Path

from lemming.agents import Agent, AgentCredits, AgentModel, AgentPermissions, AgentSchedule, FileAccess
from lemming.tools import _is_path_allowed


def test_explicit_empty_file_access_blocks_workspace(monkeypatch, tmp_path: Path):
    agent = Agent(
        name="sandboxed",
        path=Path("/tmp"),
        title="",
        short_description="",
        workflow_description="",
        model=AgentModel(),
        permissions=AgentPermissions(read_outboxes=[], send_outboxes=None, tools=[], file_access=FileAccess([], [])),
        schedule=AgentSchedule(),
        instructions="",
        credits=AgentCredits(),
        resume_path=Path("/tmp/resume.json"),
    )

    monkeypatch.setattr("lemming.agents.load_agent", lambda *_args, **_kwargs: agent)

    base_path = tmp_path
    target = (base_path / "agents" / agent.name / "workspace" / "file.txt").resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    assert _is_path_allowed(base_path, agent.name, target, "read") is False
