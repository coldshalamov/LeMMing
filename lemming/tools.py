"""Tool framework for agent capabilities."""

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
from .paths import validate_agent_name


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str | None = None


class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        """Execute the tool on behalf of an agent."""
        raise NotImplementedError


class ToolRegistry:
    """Registry of available tools."""

    _tools: dict[str, Tool] = {}

    @classmethod
    def register(cls, tool: Tool) -> None:
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> Tool | None:
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> list[str]:
        return list(cls._tools.keys())

    @classmethod
    def list_tool_info(cls) -> list[dict[str, str]]:
        return [
            {"id": tool.name, "description": tool.description}
            for tool in sorted(cls._tools.values(), key=lambda t: t.name)
        ]

    @classmethod
    def clear(cls) -> None:
        cls._tools.clear()


def _get_allowed_paths(base_path: Path, agent_name: str) -> list[Path]:
    """Get allowed paths for an agent.

    Agents are sandboxed to their own workspace plus the shared directory. This
    keeps file operations deterministic without additional per-agent overrides.
    """

    workspace = (base_path / "agents" / agent_name / "workspace").resolve()
    shared = (base_path / "shared").resolve()
    return [workspace, shared]


def _resolve_path(base_path: Path, agent_name: str, path: str) -> Path:
    """Resolve a path to absolute, canonicalized form."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (base_path / "agents" / agent_name / "workspace" / candidate).resolve()
    else:
        candidate = candidate.resolve()
    return candidate


def _is_path_allowed(base_path: Path, agent_name: str, path: Path, mode: str) -> bool:
    """Check if an agent has permission to access a path.

    Args:
        base_path: Repository base path
        agent_name: Name of the agent
        path: Path to check (will be canonicalized)
        mode: Either "read" or "write"

    Returns:
        True if access is allowed, False otherwise
    """
    # Canonicalize the target path (resolve symlinks, normalize)
    canonical_path = path.resolve()

    # Get allowed paths for this mode
    allowed_paths = _get_allowed_paths(base_path, agent_name)

    # Check if canonical path has a prefix match with any allowed path
    for allowed in allowed_paths:
        try:
            canonical_path.relative_to(allowed)
            return True
        except ValueError:
            continue

    return False


class FileReadTool(Tool):
    name = "file_read"
    description = "Read files from the agent workspace or shared directory."
    MAX_READ_SIZE = 50 * 1024  # 50KB

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        path_arg = kwargs.get("path")
        if not path_arg:
            return ToolResult(False, "", "Missing path")
        target = _resolve_path(base_path, agent_name, str(path_arg))
        if not _is_path_allowed(base_path, agent_name, target, "read"):
            return ToolResult(False, "", f"Access denied: read permission denied for {path_arg}")
        if not target.exists() or not target.is_file():
            return ToolResult(False, "", "File not found")

        try:
            # Check file size before reading
            size = target.stat().st_size
            if size > self.MAX_READ_SIZE:
                return ToolResult(False, "", f"File too large ({size} bytes). Max size is {self.MAX_READ_SIZE} bytes.")

            content = target.read_text(encoding="utf-8")
            return ToolResult(True, content)
        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(False, "", f"Failed to read file: {exc}")


class FileWriteTool(Tool):
    name = "file_write"
    description = "Write files into the agent workspace or shared directory."

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        path_arg = kwargs.get("path")
        content = kwargs.get("content", "")
        if not path_arg:
            return ToolResult(False, "", "Missing path")
        target = _resolve_path(base_path, agent_name, str(path_arg))
        if not _is_path_allowed(base_path, agent_name, target, "write"):
            return ToolResult(False, "", f"Access denied: write permission denied for {path_arg}")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(content), encoding="utf-8")
            return ToolResult(True, f"Wrote to {target}")
        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(False, "", f"Failed to write file: {exc}")


class FileListTool(Tool):
    name = "file_list"
    description = "List directory contents within the workspace or shared directory."
    MAX_ITEMS = 1000

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        path_arg = kwargs.get("path", ".")
        target_dir = _resolve_path(base_path, agent_name, str(path_arg))
        if not _is_path_allowed(base_path, agent_name, target_dir, "read"):
            return ToolResult(False, "", f"Access denied: read permission denied for {path_arg}")
        if not target_dir.exists() or not target_dir.is_dir():
            return ToolResult(False, "", "Directory not found")

        # Use os.scandir for efficiency and to stop early
        items = []
        count = 0
        import os

        try:
            with os.scandir(target_dir) as it:
                for entry in it:
                    items.append(entry.name)
                    count += 1
                    if count >= self.MAX_ITEMS:
                        break
        except OSError as e:
            return ToolResult(False, "", f"Failed to list directory: {e}")

        items.sort()
        if count >= self.MAX_ITEMS:
            items.append(f"\n... (truncated, limit {self.MAX_ITEMS})")

        return ToolResult(True, "\n".join(items))


class ShellTool(Tool):
    name = "shell"
    description = "Execute shell commands in the agent workspace."
    ALLOWED_EXECUTABLES = {"grep", "ls", "cat", "echo", "head", "tail", "jq"}
    MAX_OUTPUT_SIZE = 50 * 1024  # 50KB

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        cmd = kwargs.get("command")
        if not cmd:
            return ToolResult(False, "", "Missing command")

        try:
            args = shlex.split(cmd)
        except ValueError as e:
            return ToolResult(False, "", f"Invalid command format: {e}")

        if not args:
            return ToolResult(False, "", "Empty command")

        exe = Path(args[0]).name
        if exe not in self.ALLOWED_EXECUTABLES:
            return ToolResult(
                False,
                "",
                f"Security violation: '{exe}' is not in the allowed executables list.",
            )

        # Security checks
        # Allow first arg (executable) to be absolute (e.g. /usr/bin/python)
        # Check subsequent args for absolute paths or traversal attempts
        for i, arg in enumerate(args):
            # Check for directory traversal in any argument
            if ".." in arg:
                # Parse as potential option=value
                parts = arg.split("=", 1)
                value = parts[-1]  # Check value part (or whole arg if no =)

                # Check for traversal in the value
                if value == ".." or value.startswith("../") or value.endswith("/..") or "/../" in value:
                    return ToolResult(False, "", f"Security violation: directory traversal '{arg}' not allowed")

            # Block absolute paths in arguments (allow only for the command itself at index 0)
            if i > 0:
                parts = arg.split("=", 1)
                value = parts[-1]
                if Path(value).is_absolute():
                    return ToolResult(False, "", f"Security violation: absolute path argument '{arg}' not allowed")

        workspace = (base_path / "agents" / agent_name / "workspace").resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        try:
            # shell=False to prevent command injection chaining
            # Use PIPE to control output size manually
            process = subprocess.Popen(
                args,
                cwd=workspace,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            try:
                # Read stdout/stderr with limits
                stdout_data, stderr_data = process.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                return ToolResult(False, "", "Command timed out")

            success = process.returncode == 0

            # Truncate output if needed
            if len(stdout_data) > self.MAX_OUTPUT_SIZE:
                stdout_data = stdout_data[: self.MAX_OUTPUT_SIZE] + f"\n... (truncated, limit {self.MAX_OUTPUT_SIZE})"

            if len(stderr_data) > self.MAX_OUTPUT_SIZE:
                stderr_data = stderr_data[: self.MAX_OUTPUT_SIZE] + f"\n... (truncated, limit {self.MAX_OUTPUT_SIZE})"

            return ToolResult(success, stdout_data.strip(), stderr_data if not success else None)

        except FileNotFoundError:
            return ToolResult(False, "", f"Command not found: {args[0]}")
        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(False, "", f"Shell execution failed: {exc}")


class MemoryReadTool(Tool):
    name = "memory_read"
    description = "Read a key from the agent's memory store."

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        key = kwargs.get("key")
        if not key:
            return ToolResult(False, "", "Missing key")
        value = memory.load_memory(base_path, agent_name, str(key))
        if value is None:
            return ToolResult(False, "", "Memory not found")
        return ToolResult(True, json.dumps(value))


class MemoryWriteTool(Tool):
    name = "memory_write"
    description = "Write a key/value pair into the agent's memory store."

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        key = kwargs.get("key")
        value = kwargs.get("value")
        if not key:
            return ToolResult(False, "", "Missing key")
        try:
            memory.save_memory(base_path, agent_name, str(key), value)
            return ToolResult(True, f"Saved memory for {key}")
        except ValueError as e:
            return ToolResult(False, "", f"Invalid memory key: {e}")
        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(False, "", f"Failed to save memory: {exc}")


class CreateAgentTool(Tool):
    name = "create_agent"
    description = "Create a new agent from the agent template."

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        new_agent_name = kwargs.get("name")
        if not new_agent_name:
            return ToolResult(False, "", "Missing new agent name")

        try:
            validate_agent_name(new_agent_name)
        except ValueError as e:
            return ToolResult(False, "", f"Invalid agent name: {e}")

        new_agent_path = base_path / "agents" / str(new_agent_name)
        if new_agent_path.exists():
            return ToolResult(False, "", "Agent already exists")
        template_path = base_path / "agents" / "agent_template"
        if not template_path.exists():
            return ToolResult(False, "", "Agent template missing")
        try:
            shutil.copytree(template_path, new_agent_path)
            resume_path = new_agent_path / "resume.json"
            if resume_path.exists():
                data = json.loads(resume_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    data["name"] = str(new_agent_name)
                    resume_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return ToolResult(True, f"Created agent {new_agent_name}")
        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(False, "", f"Failed to create agent: {exc}")


class ListAgentsTool(Tool):
    name = "list_agents"
    description = "List all agents and basic information."

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:  # noqa: ARG002
        from .agents import discover_agents

        agents = discover_agents(base_path)
        info = [{"name": ag.name, "title": ag.title, "description": ag.short_description} for ag in agents]
        return ToolResult(True, json.dumps(info, indent=2))


# Register default tools
ToolRegistry.register(FileReadTool())
ToolRegistry.register(FileWriteTool())
ToolRegistry.register(FileListTool())
ToolRegistry.register(ShellTool())
ToolRegistry.register(MemoryReadTool())
ToolRegistry.register(MemoryWriteTool())
ToolRegistry.register(CreateAgentTool())
ToolRegistry.register(ListAgentsTool())
