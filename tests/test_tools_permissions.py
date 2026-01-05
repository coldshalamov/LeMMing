from __future__ import annotations

from pathlib import Path

from lemming.tools import _is_path_allowed


def test_paths_are_sandboxed_to_workspace_and_shared(tmp_path: Path) -> None:
    agent_name = "sandboxed"
    base_path = tmp_path

    workspace_target = (base_path / "agents" / agent_name / "workspace" / "file.txt").resolve()
    shared_target = (base_path / "shared" / "shared.txt").resolve()
    other_target = (base_path / "other" / "escape.txt").resolve()

    workspace_target.parent.mkdir(parents=True, exist_ok=True)
    shared_target.parent.mkdir(parents=True, exist_ok=True)
    other_target.parent.mkdir(parents=True, exist_ok=True)

    assert _is_path_allowed(base_path, agent_name, workspace_target, "read") is True
    assert _is_path_allowed(base_path, agent_name, shared_target, "write") is True
    assert _is_path_allowed(base_path, agent_name, other_target, "read") is False
