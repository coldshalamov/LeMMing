
import shutil
from pathlib import Path
from lemming.tools import FileWriteTool
from lemming.paths import get_agents_dir

def test_nested_agent_workspace_isolation(tmp_path):
    """
    Verify that nested agents (e.g. agents/subdir/name) access their own workspace
    and do not hijack the workspace of a root agent with the same name (agents/name).
    """
    base_path = tmp_path

    agents_dir = get_agents_dir(base_path)
    agents_dir.mkdir(parents=True)

    # 1. Create a "victim" agent at root
    victim_dir = agents_dir / "victim"
    victim_dir.mkdir()
    (victim_dir / "workspace").mkdir()

    # 2. Create an "attacker" agent nested in "subdir"
    attacker_dir = agents_dir / "subdir" / "victim" # Same name "victim"
    attacker_dir.mkdir(parents=True)
    (attacker_dir / "workspace").mkdir()

    # 3. Simulate attacker running FileWriteTool
    tool = FileWriteTool()

    # The engine passes agent_path=attacker_dir
    result = tool.execute(
        agent_name="victim",
        base_path=base_path,
        path="test_file.txt",
        content="data",
        agent_path=attacker_dir
    )

    assert result.success

    # 4. Check where the file landed
    victim_file = victim_dir / "workspace" / "test_file.txt"
    attacker_file = attacker_dir / "workspace" / "test_file.txt"

    # It SHOULD be in attacker's workspace
    assert attacker_file.exists(), "File should be written to nested agent's workspace"

    # It SHOULD NOT be in victim's workspace
    assert not victim_file.exists(), "File should NOT be written to root agent's workspace"

def test_legacy_agent_workspace_fallback(tmp_path):
    """
    Verify that if agent_path is NOT provided (legacy/external call),
    it falls back to standard resolution (which might be ambiguous but preserves behavior).
    """
    base_path = tmp_path
    agents_dir = get_agents_dir(base_path)
    agents_dir.mkdir(parents=True)

    # Create root agent
    root_dir = agents_dir / "legacy"
    root_dir.mkdir()
    (root_dir / "workspace").mkdir()

    tool = FileWriteTool()

    # No agent_path provided
    result = tool.execute(
        agent_name="legacy",
        base_path=base_path,
        path="legacy.txt",
        content="legacy"
    )

    assert result.success
    assert (root_dir / "workspace" / "legacy.txt").exists()
