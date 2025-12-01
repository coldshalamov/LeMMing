from pathlib import Path

from lemming import memory
from lemming.agents import Agent
from lemming.engine import _build_prompt, _execute_tools
from lemming.tools import (
    FileReadTool,
    Tool,
    ToolRegistry,
)


def test_tool_registry_register_and_lookup():
    class DummyTool(Tool):
        name = "dummy_tool"
        description = "test"

        def execute(self, agent_name: str, base_path: Path, **kwargs):  # type: ignore[override]
            return None

    ToolRegistry.register(DummyTool())
    assert "dummy_tool" in ToolRegistry.list_tools()
    assert isinstance(ToolRegistry.get("dummy_tool"), DummyTool)


def test_file_read_scope(tmp_path: Path):
    base_path = tmp_path
    agent_name = "tester"
    workspace = base_path / "agents" / agent_name / "workspace"
    workspace.mkdir(parents=True)
    allowed_file = workspace / "note.txt"
    allowed_file.write_text("ok", encoding="utf-8")

    outside_file = base_path / "secret.txt"
    outside_file.write_text("forbidden", encoding="utf-8")

    tool = FileReadTool()
    result_allowed = tool.execute(agent_name, base_path, path="note.txt")
    assert result_allowed.success
    assert result_allowed.output == "ok"

    result_denied = tool.execute(agent_name, base_path, path="../secret.txt")
    assert not result_denied.success
    assert "Access denied" in (result_denied.error or "")


def test_execute_tools_permission_enforced(tmp_path: Path):
    agent_path = tmp_path / "agents" / "a1"
    agent_path.mkdir(parents=True)
    agent = Agent(
        name="a1",
        path=agent_path,
        model_key="m1",
        org_speed_multiplier=1,
        send_to=[],
        read_from=[],
        max_credits=0,
        resume_text="",
        instructions_text="",
        config_json={},
        role="",
        description="",
    )

    results = _execute_tools(
        tmp_path,
        agent,
        [
            {
                "tool": "file_read",
                "args": {"path": "note.txt"},
            }
        ],
    )
    assert len(results) == 1
    assert not results[0].success
    assert "not permitted" in (results[0].error or "")


def test_memory_context_in_prompt(tmp_path: Path):
    agent_path = tmp_path / "agents" / "memo"
    agent_path.mkdir(parents=True)
    memory.save_memory(tmp_path, "memo", "fact", {"data": 1})

    agent = Agent(
        name="memo",
        path=agent_path,
        model_key="m1",
        org_speed_multiplier=1,
        send_to=[],
        read_from=[],
        max_credits=0,
        resume_text="",
        instructions_text="",
        config_json={},
        role="",
        description="",
    )

    prompt = _build_prompt(tmp_path, agent, [])
    memory_messages = [p for p in prompt if "MEMORY CONTEXT" in p.get("content", "")]
    assert memory_messages
    assert "fact" in memory_messages[0]["content"]

