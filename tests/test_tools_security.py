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
    result = tool.execute(agent_name="hr", base_path=base_path, name=malicious_name)  # Must be hr to use this tool

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


def test_shell_tool_prohibits_python(tmp_path):
    """Ensure python execution is blocked by ShellTool."""
    base_path = tmp_path / "lemming"
    agents_dir = base_path / "agents"
    agent_name = "tester"
    agent_dir = agents_dir / agent_name
    workspace = agent_dir / "workspace"
    workspace.mkdir(parents=True)

    tool = ShellTool()

    # Attempt to run python
    command = "python -c 'print(\"hello\")'"

    result = tool.execute(agent_name=agent_name, base_path=base_path, command=command)

    assert not result.success
    assert "security violation" in result.error.lower()
    assert "python" in result.error.lower()


def test_shell_tool_sandbox_arguments(tmp_path):
    """Ensure ShellTool blocks traversal in arguments."""
    base_path = tmp_path / "lemming"
    agents_dir = base_path / "agents"
    agent_name = "tester"
    agent_dir = agents_dir / agent_name
    workspace = agent_dir / "workspace"
    workspace.mkdir(parents=True)

    tool = ShellTool()

    # Attempt traversal in argument
    command = "cat ../../../secrets.json"

    result = tool.execute(agent_name=agent_name, base_path=base_path, command=command)

    assert not result.success
    assert "security violation" in result.error.lower()
    assert "directory traversal" in result.error.lower()


def test_shell_tool_absolute_path_argument(tmp_path):
    """Ensure ShellTool blocks absolute paths in arguments."""
    base_path = tmp_path / "lemming"
    agents_dir = base_path / "agents"
    agent_name = "tester"
    agent_dir = agents_dir / agent_name
    workspace = agent_dir / "workspace"
    workspace.mkdir(parents=True)

    tool = ShellTool()

    # Attempt absolute path
    command = "cat /etc/passwd"

    result = tool.execute(agent_name=agent_name, base_path=base_path, command=command)

    assert not result.success
    assert "security violation" in result.error.lower()
    assert "absolute path" in result.error.lower()
