"""Tools that agents can use during execution.

Each tool must inherit from Tool and implement the execute method.
All tools are registered in ToolRegistry for discovery and execution.
"""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import memory
from .paths import get_agent_dir, get_agents_dir, validate_agent_name


def _is_path_allowed(base_path: Path, agent_name: str, target_path: Path, mode: str) -> bool:
    """Check if an agent is allowed to access a given path.

    Args:
        base_path: Base path of the LeMMing workspace
        agent_name: Name of the agent
        target_path: Path to check access for
        mode: Access mode ("read" or "write") - reserved for future use

    Returns:
        True if access is allowed, False otherwise

    Note:
        The 'mode' parameter is reserved for future use to implement
        different permissions for read vs write operations.
    """
    # Resolve paths to handle symlinks and relative paths
    try:
        resolved_target = target_path.resolve()
        resolved_base = base_path.resolve()
    except Exception:
        return False

    # Agents can access their own workspace
    agent_workspace = (resolved_base / "agents" / agent_name / "workspace").resolve()
    if resolved_target.is_relative_to(agent_workspace):
        return True

    # Agents can access the shared directory
    shared_dir = (resolved_base / "shared").resolve()
    if resolved_target.is_relative_to(shared_dir):
        return True

    # All other paths are denied
    return False


@dataclass
class ToolResult:
    """Result of tool execution."""

    success: bool
    output: str = ""
    error: str = ""


class Tool(ABC):
    """Base class for all tools."""

    name: str
    description: str

    @abstractmethod
    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        """Execute the tool with given arguments.

        Args:
            agent_name: Name of the agent executing the tool
            base_path: Base path of the LeMMing workspace
            **kwargs: Tool-specific arguments

        Returns:
            ToolResult with success status, output, and error message
        """
        pass


class ToolRegistry:
    """Registry for all available tools.

    This is a class-level registry that maintains a global mapping of tool names
    to tool instances. The _tools dict is intentionally shared across all instances
    as part of the singleton registry pattern.
    """

    _tools: dict[str, Tool] = {}

    @classmethod
    def register(cls, tool: Tool) -> None:
        """Register a tool."""
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> Tool | None:
        """Get a tool by name."""
        return cls._tools.get(name)

    @classmethod
    def list_tool_info(cls) -> list[dict[str, str]]:
        """List all registered tools with their metadata."""
        return [{"id": name, "description": tool.description} for name, tool in cls._tools.items()]


class MemoryReadTool(Tool):
    """Tool for reading from agent memory."""

    name = "memory_read"
    description = "Read a value from the agent's memory store by key."

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        key = kwargs.get("key")
        if not key:
            return ToolResult(False, "", "Missing key")

        try:
            value = memory.load_memory(base_path, agent_name, str(key))
            if value is None:
                return ToolResult(False, "", f"Memory key '{key}' not found")
            return ToolResult(True, json.dumps(value))
        except ValueError as e:
            return ToolResult(False, "", f"Invalid memory key: {e}")
        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(False, "", f"Failed to read memory: {exc}")


class MemoryWriteTool(Tool):
    """Tool for writing key/value pairs to agent memory with size limits."""

    name = "memory_write"
    description = "Write a key/value pair into the agent's memory store."
    MAX_MEMORY_SIZE = 50 * 1024  # 50KB

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        key = kwargs.get("key")
        value = kwargs.get("value")
        if not key:
            return ToolResult(False, "", "Missing key")

        # Check size of value when serialized
        try:
            serialized = json.dumps(value)
            if len(serialized) > self.MAX_MEMORY_SIZE:
                return ToolResult(
                    False,
                    "",
                    f"Memory value too large ({len(serialized)} bytes). Max size is {self.MAX_MEMORY_SIZE} bytes.",
                )
        except (TypeError, ValueError):
            return ToolResult(False, "", "Memory value is not JSON serializable")

        try:
            memory.save_memory(base_path, agent_name, str(key), value)
            return ToolResult(True, f"Saved memory for {key}")
        except ValueError as e:
            return ToolResult(False, "", f"Invalid memory key: {e}")
        except Exception as e:
            return ToolResult(False, "", f"Failed to save memory: {e}")


class CreateAgentTool(Tool):
    """Tool for creating new agents from the template."""

    name = "create_agent"
    description = "Create a new agent from the agent template."

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        # Only HR agent can create agents
        if agent_name != "hr":
            return ToolResult(False, "", "Only the 'hr' agent can create new agents")

        new_agent_name = kwargs.get("name")
        if not new_agent_name:
            return ToolResult(False, "", "Missing 'name' parameter")

        # Validate agent name for security (reuse centralized validation)
        if not isinstance(new_agent_name, str):
            return ToolResult(False, "", "Agent name must be a string")

        try:
            validate_agent_name(new_agent_name)
        except ValueError as e:
            return ToolResult(False, "", str(e))

        agents_dir = get_agents_dir(base_path)
        template_dir = agents_dir / "agent_template"
        new_agent_dir = agents_dir / new_agent_name

        # Check if template exists
        if not template_dir.exists():
            return ToolResult(False, "", "Agent template not found")

        # Check if agent already exists
        if new_agent_dir.exists():
            return ToolResult(False, "", f"Agent '{new_agent_name}' already exists")

        # Resolve paths and verify they're within the agents directory
        try:
            resolved_new = new_agent_dir.resolve()
            resolved_agents = agents_dir.resolve()

            # Ensure the new agent directory is within the agents directory
            if not resolved_new.is_relative_to(resolved_agents):
                return ToolResult(False, "", "Security violation: path traversal attempt detected")
        except Exception as e:
            return ToolResult(False, "", f"Path validation error: {e}")

        # Copy template to new agent directory
        try:
            shutil.copytree(template_dir, new_agent_dir)
            return ToolResult(True, f"Created agent '{new_agent_name}' from template")
        except Exception as e:
            return ToolResult(False, "", f"Failed to create agent: {e}")


class FileWriteTool(Tool):
    """Tool for writing files in agent workspace or shared directory."""

    name = "file_write"
    description = "Write content to a file in the agent's workspace or shared directory."
    MAX_FILE_SIZE = 100 * 1024  # 100KB

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        path_str = kwargs.get("path")
        content = kwargs.get("content")

        if not path_str:
            return ToolResult(False, "", "Missing 'path' parameter")
        if content is None:
            return ToolResult(False, "", "Missing 'content' parameter")

        if not isinstance(content, str):
            return ToolResult(False, "", "Content must be a string")

        # Check file size
        if len(content) > self.MAX_FILE_SIZE:
            return ToolResult(
                False,
                "",
                f"File content too large ({len(content)} bytes). Max size is {self.MAX_FILE_SIZE} bytes.",
            )

        # Determine target path (workspace or shared)
        agent_dir = get_agent_dir(base_path, agent_name)
        workspace_dir = agent_dir / "workspace"

        # If path starts with "shared/", write to shared directory
        if path_str.startswith("shared/"):
            target_path = base_path / path_str
        else:
            target_path = workspace_dir / path_str

        # Security check: ensure path is allowed
        if not _is_path_allowed(base_path, agent_name, target_path, "write"):
            return ToolResult(False, "", "Security violation: path is outside allowed directories")

        # Ensure parent directory exists
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return ToolResult(False, "", f"Failed to create parent directory: {e}")

        # Write file
        try:
            target_path.write_text(content, encoding="utf-8")
            return ToolResult(True, f"Wrote {len(content)} bytes to {path_str}")
        except Exception as e:
            return ToolResult(False, "", f"Failed to write file: {e}")


class ShellTool(Tool):
    """Tool for executing shell commands in agent workspace."""

    name = "shell"
    description = (
        "Execute a shell command in the agent's workspace directory. "
        "Allowed: grep, ls, cat, echo, head, tail, jq."
    )

    ALLOWED_COMMANDS = {"grep", "ls", "cat", "echo", "head", "tail", "jq"}

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        command = kwargs.get("command")
        if not command:
            return ToolResult(False, "", "Missing 'command' parameter")

        if not isinstance(command, str):
            return ToolResult(False, "", "Command must be a string")

        # Parse command
        try:
            args = shlex.split(command)
        except ValueError as e:
            return ToolResult(False, "", f"Invalid command format: {e}")

        if not args:
            return ToolResult(False, "", "Empty command")

        # Check against allowlist
        executable = args[0]
        if executable not in self.ALLOWED_COMMANDS:
            allowed = ", ".join(sorted(self.ALLOWED_COMMANDS))
            return ToolResult(False, "", f"Command '{executable}' is not allowed. Allowed: {allowed}")

        # Check arguments for traversal/absolute paths
        for arg in args[1:]:
             # Check for directory traversal
            if ".." in arg:
                return ToolResult(False, "", "Security violation: directory traversal detected in arguments")

            # Check for absolute paths
            # We strictly prohibit absolute paths to ensure agents are confined to their workspace.
            # Using pathlib.Path.is_absolute covers both Unix (/) and Windows (C:\) absolute paths.
            if Path(arg).is_absolute():
                 return ToolResult(False, "", "Security violation: absolute path detected in arguments")

        # Get agent workspace directory
        agent_dir = get_agent_dir(base_path, agent_name)
        workspace_dir = agent_dir / "workspace"

        # Ensure workspace exists
        if not workspace_dir.exists():
            workspace_dir.mkdir(parents=True, exist_ok=True)

        # Execute command in workspace
        try:
            # shell=False ensures we execute exactly what we parsed
            result = subprocess.run(
                args,
                shell=False,
                cwd=workspace_dir,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
            )

            if result.returncode == 0:
                return ToolResult(True, result.stdout)
            else:
                return ToolResult(False, result.stdout, result.stderr)
        except FileNotFoundError:
             return ToolResult(False, "", f"Command '{executable}' not found in system")
        except subprocess.TimeoutExpired:
            return ToolResult(False, "", "Command timed out after 30 seconds")
        except Exception as e:
            return ToolResult(False, "", f"Failed to execute command: {e}")


# Register all tools
ToolRegistry.register(MemoryReadTool())
ToolRegistry.register(MemoryWriteTool())
ToolRegistry.register(CreateAgentTool())
ToolRegistry.register(FileWriteTool())
ToolRegistry.register(ShellTool())
