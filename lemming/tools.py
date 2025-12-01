"""Tool framework for agent capabilities."""

from __future__ import annotations

import json
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import memory


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
    def clear(cls) -> None:
        cls._tools.clear()


def _allowed_paths(base_path: Path, agent_name: str) -> list[Path]:
    workspace = (base_path / "agents" / agent_name / "workspace").resolve()
    shared = (base_path / "shared").resolve()
    return [workspace, shared]


def _resolve_path(base_path: Path, agent_name: str, path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (base_path / "agents" / agent_name / "workspace" / candidate).resolve()
    else:
        candidate = candidate.resolve()
    return candidate


def _is_path_allowed(base_path: Path, agent_name: str, path: Path) -> bool:
    path = path.resolve()
    for allowed in _allowed_paths(base_path, agent_name):
        try:
            path.relative_to(allowed)
            return True
        except ValueError:
            continue
    return False


class FileReadTool(Tool):
    name = "file_read"
    description = "Read files from the agent workspace or shared directory."

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        path_arg = kwargs.get("path")
        if not path_arg:
            return ToolResult(False, "", "Missing path")
        target = _resolve_path(base_path, agent_name, str(path_arg))
        if not _is_path_allowed(base_path, agent_name, target):
            return ToolResult(False, "", "Access denied to path")
        if not target.exists() or not target.is_file():
            return ToolResult(False, "", "File not found")
        try:
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
        if not _is_path_allowed(base_path, agent_name, target):
            return ToolResult(False, "", "Access denied to path")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(content), encoding="utf-8")
            return ToolResult(True, f"Wrote to {target}")
        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(False, "", f"Failed to write file: {exc}")


class FileListTool(Tool):
    name = "file_list"
    description = "List directory contents within the workspace or shared directory."

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        path_arg = kwargs.get("path", ".")
        target_dir = _resolve_path(base_path, agent_name, str(path_arg))
        if not _is_path_allowed(base_path, agent_name, target_dir):
            return ToolResult(False, "", "Access denied to path")
        if not target_dir.exists() or not target_dir.is_dir():
            return ToolResult(False, "", "Directory not found")
        items = sorted(p.name for p in target_dir.iterdir())
        return ToolResult(True, "\n".join(items))


class ShellTool(Tool):
    name = "shell"
    description = "Execute shell commands in the agent workspace."

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        cmd = kwargs.get("command")
        if not cmd:
            return ToolResult(False, "", "Missing command")
        workspace = (base_path / "agents" / agent_name / "workspace").resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                cmd,
                cwd=workspace,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            success = result.returncode == 0
            error_text = result.stderr if not success else None
            output = result.stdout.strip()
            return ToolResult(success, output, error_text)
        except subprocess.TimeoutExpired:
            return ToolResult(False, "", "Command timed out")
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
        memory.save_memory(base_path, agent_name, str(key), value)
        return ToolResult(True, f"Saved memory for {key}")


class CreateAgentTool(Tool):
    name = "create_agent"
    description = "Create a new agent from the agent template."

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        if agent_name != "hr":
            return ToolResult(False, "", "Tool restricted to hr agent")
        new_agent_name = kwargs.get("name")
        if not new_agent_name:
            return ToolResult(False, "", "Missing new agent name")
        new_agent_path = base_path / "agents" / str(new_agent_name)
        if new_agent_path.exists():
            return ToolResult(False, "", "Agent already exists")
        template_path = base_path / "agents" / "agent_template"
        if not template_path.exists():
            return ToolResult(False, "", "Agent template missing")
        try:
            shutil.copytree(template_path, new_agent_path)
            return ToolResult(True, f"Created agent {new_agent_name}")
        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(False, "", f"Failed to create agent: {exc}")


# Register default tools
ToolRegistry.register(FileReadTool())
ToolRegistry.register(FileWriteTool())
ToolRegistry.register(FileListTool())
ToolRegistry.register(ShellTool())
ToolRegistry.register(MemoryReadTool())
ToolRegistry.register(MemoryWriteTool())
ToolRegistry.register(CreateAgentTool())

