from lemming.tools import CreateAgentTool, ShellTool


def test_create_agent_path_traversal(tmp_path):
    # Setup
    base_path = tmp_path / "lemming"
    agents_dir = base_path / "agents"
    agents_dir.mkdir(parents=True)

    # Create template
    template_path = agents_dir / "agent_template"
    template_path.mkdir()
    (template_path / "resume.json").touch()

    tool = CreateAgentTool()

    # Attempt traversal
    # We try to create an agent named "../evil" which should resolve to
    # base_path / "evil" (outside of agents directory)
    malicious_name = "../evil"

    # Execute
    result = tool.execute(
        agent_name="hr",  # Must be hr to use this tool
        base_path=base_path,
        name=malicious_name,
    )

    # Check if directory was created outside agents dir
    evil_path = base_path / "evil"

    # If the tool is vulnerable, it might return success OR fail if the target dir doesn't exist etc.
    # But checking if the path was created is the key.

    # However, shutil.copytree requires parent of destination to exist.
    # base_path / "agents" / "../evil" -> base_path / "evil".
    # base_path exists. So "evil" directory should be created inside base_path.

    assert not evil_path.exists(), f"Path traversal succeeded! Created directory at {evil_path}"

    # The tool should ideally fail gracefully
    assert not result.success
    assert "invalid" in result.error.lower() or "security" in result.error.lower()


def test_shell_tool_blocks_python(tmp_path):
    """Verify that python execution is blocked."""
    base_path = tmp_path
    agents_dir = base_path / "agents" / "tester"
    agents_dir.mkdir(parents=True)
    workspace = agents_dir / "workspace"
    workspace.mkdir(parents=True)

    tool = ShellTool()

    # Python one-liner
    cmd = "python -c \"print('hello')\""

    result = tool.execute(agent_name="tester", base_path=base_path, command=cmd)

    assert not result.success
    assert "Security violation" in result.error
    assert "'python' is not in the allowed executables list" in result.error
