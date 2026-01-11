

class MemoryWriteTool(Tool):
    name = "memory_write"
    description = "Write a key/value pair into the agent's memory store."
    MAX_MEMORY_SIZE = 50 * 1024  # 50KB

    def execute(self, agent_name: str, base_path: Path, **kwargs: Any) -> ToolResult:
        key = kwargs.get("key")
        value = kwargs.get("value")
        if not key:
            return ToolResult(False, "", "Missing key")

        # Check serialized size
        try:
            serialized = json.dumps(value)
            if len(serialized) > self.MAX_MEMORY_SIZE:
                return ToolResult(
                    False,
                    "",
                    f"Memory value too large ({len(serialized)} bytes). Max size is {self.MAX_MEMORY_SIZE} bytes.",
                )
        except (TypeError, ValueError) as e:
            return ToolResult(False, "", f"Invalid memory value (not JSON serializable): {e}")

        # Check key format validity via save_memory call or pre-check
        # save_memory will handle the save, but we validated size
        try:
            memory.save_memory(base_path, agent_name, str(key), value)
            return ToolResult(True, f"Saved memory for {key}")
        except ValueError as e:
            return ToolResult(False, "", f"Invalid memory key: {e}")
        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(False, "", f"Failed to save memory: {exc}")


class CreateAgentTool(Tool):