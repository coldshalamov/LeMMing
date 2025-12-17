# LeMMing Architecture Guide

## Table of Contents

1. [Core Principles](#core-principles)
2. [System Components](#system-components)
3. [Data Flow](#data-flow)
4. [Scheduling & Execution](#scheduling--execution)
5. [Message Passing](#message-passing)
6. [Memory System](#memory-system)
7. [File Structure](#file-structure)

---

## Core Principles

LeMMing is built on **five absolute invariants** that define its architecture:

### 1. Filesystem is Truth

All state lives in the filesystem. No hidden databases, no in-memory-only state.

```
agents/
  <agent_name>/
    resume.json          # Agent configuration (source of truth)
    outbox/              # Messages written by this agent
    memory/              # Key-value memory store
    workspace/           # Agent's working directory
    logs/                # Activity logs
```

**Why?**: Filesystem-first design enables:
- Easy debugging (inspect state with `ls`, `cat`, `jq`)
- Version control integration (git track agent state)
- Horizontal scalability (shared filesystem)
- Disaster recovery (backup = cp -r)

### 2. Resume is the ABI

Each agent is completely defined by `agents/<name>/resume.json`:

```json
{
  "name": "planner",
  "title": "Strategic Planner",
  "model": {"key": "gpt-4o-mini", "temperature": 0.2},
  "permissions": {
    "read_outboxes": ["*"],
    "tools": ["file_read", "memory_write"],
    "file_access": {
      "allow_read": ["./workspace", "./shared"],
      "allow_write": ["./workspace"]
    }
  },
  "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},
  "instructions": "You are a strategic planner...",
  "credits": {"max_credits": 1000, "soft_cap": 500}
}
```

The engine reads **ONLY** `resume.json` - no hardcoded agent roles.

### 3. Outbox-Only Messaging

Agents communicate via the **outbox pattern**:

- Agents write **ONLY** to their own `outbox/`
- Agents read from other agents' outboxes (if permitted)
- No direct agent-to-agent writes
- Engine assembles "virtual inbox" from readable outboxes

**Why?**: Prevents race conditions, maintains clear audit trail, enables message replay.

### 4. Tick-Based Scheduler

Execution is driven by discrete **ticks** (logical time steps):

```python
# Agent fires when: (tick + phase_offset) % run_every_n_ticks == 0
should_run(agent, tick=10) → (10 + 0) % 1 == 0 → True  # Every tick
should_run(agent, tick=10) → (10 + 1) % 3 == 0 → False # Every 3 ticks, offset by 1
```

**Intra-tick ordering** (deterministic):
1. Compute `fire_point = (-phase_offset mod N) / N` for each agent
2. Sort by `(fire_point, agent_name)` ascending
3. Execute in that order

**Why?**: Reproducible execution, no concurrency bugs, testable.

### 5. Engine↔LLM JSON Contract

LLM responses **MUST** follow this schema:

```json
{
  "outbox_entries": [
    {"kind": "message|report|request|response|status", "payload": {...}, "tags": [...]}
  ],
  "tool_calls": [
    {"tool": "file_read", "args": {"path": "data.txt"}}
  ],
  "memory_updates": [
    {"key": "context", "value": {...}}
  ],
  "notes": "Optional free-form notes for logs"
}
```

Engine fills in `agent`, `tick`, `timestamp` on outbox entries.

---

## System Components

### Engine (`lemming/engine.py`)

Core orchestrator that:
- Loads agents from `agents/` directory
- Determines which agents fire this tick
- Builds LLM prompts from memory + inbox
- Calls LLM provider
- Parses response and executes tools
- Writes outbox entries
- Advances tick counter

Key functions:
- `run_tick(base_path, tick)` - Execute one tick
- `run_once(base_path)` - Run one tick and persist
- `run_forever(base_path)` - Continuous execution loop
- `get_firing_agents(agents, tick)` - Determine execution order

### Agents (`lemming/agents.py`)

Agent dataclass and discovery:

```python
@dataclass
class Agent:
    name: str
    title: str
    model: AgentModel
    permissions: AgentPermissions
    schedule: AgentSchedule
    instructions: str
    credits: AgentCredits
```

Functions:
- `load_agent(base_path, name)` - Load from resume.json
- `discover_agents(base_path)` - Find all valid agents

### Messages (`lemming/messages.py`)

Outbox entry schema and I/O:

```python
@dataclass
class OutboxEntry:
    id: str
    tick: int
    agent: str
    kind: str
    payload: dict[str, Any]
    tags: list[str]
    created_at: str
```

Functions:
- `write_outbox_entry(base_path, agent_name, entry)` - Write to outbox
- `read_outbox_entries(base_path, agent_name, limit)` - Read entries
- `collect_readable_outboxes(base_path, agent_name, permissions)` - Assemble inbox
- `cleanup_old_outbox_entries(base_path, current_tick)` - Prune old messages

### Memory (`lemming/memory.py`)

Key-value store per agent:

```python
save_memory(base_path, agent_name, "goals", ["goal1", "goal2"])
goals = load_memory(base_path, agent_name, "goals")
```

Advanced features:
- `compact_memory_list()` - Trim list-based memories
- `archive_old_memories()` - Move old memories to archive/
- `append_memory_event()` - Timestamped event log with auto-compaction

### Tools (`lemming/tools.py`)

Agent capabilities:

| Tool | Description | Permission Check |
|------|-------------|------------------|
| `file_read` | Read files | `file_access.allow_read` |
| `file_write` | Write files | `file_access.allow_write` |
| `file_list` | List directory | `file_access.allow_read` |
| `shell` | Run commands | Workspace only |
| `memory_read` | Load memory | Always allowed |
| `memory_write` | Save memory | Always allowed |
| `create_agent` | Spawn agent | Restricted to `hr` |
| `list_agents` | List all agents | Always allowed |

### Providers (`lemming/providers.py`)

LLM backend abstraction:

```python
class LLMProvider(ABC):
    def call(self, model_name, messages, temperature, **kwargs) -> str:
        pass
```

Implementations:
- `OpenAIProvider` - OpenAI API (GPT models)
- `AnthropicProvider` - Anthropic Claude API
- `OllamaProvider` - Local Ollama server
- `RetryingLLMProvider` - Wrapper with exponential backoff + circuit breaker

### Logging (`lemming/logging_config.py`)

Structured JSON logging:

```python
setup_logging(base_path, level="INFO")
log_agent_action(base_path, agent_name, tick, "agent_completed", duration_ms=1234)
```

Logs:
- `logs/engine.log` - Global engine events
- `agents/<name>/logs/activity.log` - Per-agent structured logs

---

## Data Flow

### Execution Flow (Single Tick)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. LOAD TICK                                                 │
│    tick = load_tick(base_path)  # From tick.json            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. DISCOVER AGENTS                                           │
│    agents = discover_agents(base_path)                       │
│    # Load all agents/*/resume.json                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. DETERMINE FIRING AGENTS                                   │
│    firing = get_firing_agents(agents, tick)                 │
│    # Filter + sort by (fire_point, name)                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. FOR EACH AGENT (in order):                                │
│    a. Check credits                                          │
│    b. Build prompt:                                          │
│       - System preamble                                      │
│       - Agent instructions                                   │
│       - Memory context                                       │
│       - Inbox (readable outboxes)                            │
│    c. Call LLM                                               │
│    d. Parse JSON response                                    │
│    e. Write outbox entries                                   │
│    f. Execute tool calls                                     │
│    g. Update memory                                          │
│    h. Deduct credits                                         │
│    i. Log action                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. CLEANUP                                                   │
│    cleanup_old_outbox_entries(base_path, tick)               │
│    # Remove messages older than retention period             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. PERSIST TICK                                              │
│    persist_tick(base_path, tick + 1)                         │
│    # Write tick.json with incremented tick                   │
└─────────────────────────────────────────────────────────────┘
```

### Message Flow Example

```
Tick 1:
  planner → outbox/00000001_abc123.json
    {"kind": "request", "payload": {"task": "Analyze data"}}

Tick 2:
  analyst reads planner's outbox
  analyst → outbox/00000002_def456.json
    {"kind": "response", "payload": {"result": "..."}}

Tick 3:
  planner reads analyst's outbox
  planner → outbox/00000003_ghi789.json
    {"kind": "message", "payload": {"text": "Thanks!"}}
```

---

## Scheduling & Execution

### Schedule Configuration

```json
{
  "schedule": {
    "run_every_n_ticks": 3,  // Fire every 3 ticks
    "phase_offset": 1         // Offset by 1 tick
  }
}
```

**Firing condition**: `(tick + phase_offset) % run_every_n_ticks == 0`

### Fire Point Calculation

For deterministic intra-tick ordering:

```python
fire_point = ((-phase_offset) % N) / N
```

**Examples** (N=4):
- offset=0 → fire_point = 0.0
- offset=1 → fire_point = 0.75
- offset=2 → fire_point = 0.5
- offset=3 → fire_point = 0.25

Agents execute in order: `sorted(agents, key=lambda a: (fire_point(a), a.name))`

### Execution Order Guarantee

Given agents with same `run_every_n_ticks`:
1. Lower `phase_offset` → lower fire_point → runs earlier
2. Same fire_point → alphabetical by name

---

## Message Passing

### Outbox Entry Format

```json
{
  "id": "abc123def456",
  "tick": 42,
  "agent": "planner",
  "kind": "message",
  "payload": {
    "text": "Hello, analyst!",
    "target": "analyst",
    "importance": "high"
  },
  "tags": ["urgent", "follow-up"],
  "created_at": "2025-12-08T10:30:00Z"
}
```

### Message Kinds

| Kind | Purpose |
|------|---------|
| `message` | General communication |
| `report` | Status or progress updates |
| `request` | Ask another agent to do something |
| `response` | Reply to a request |
| `status` | Agent health/state notification |

### Permission Model

```json
{
  "permissions": {
    "read_outboxes": ["analyst", "coordinator", "*"],  // "*" = wildcard
    "tools": ["file_read", "memory_write"],
    "file_access": {
      "allow_read": ["./workspace", "./shared", "/data"],
      "allow_write": ["./workspace"]
    }
  }
}
```

---

## Memory System

### Memory File Format

```json
{
  "key": "goals",
  "value": ["Analyze Q4 data", "Prepare report"],
  "timestamp": "2025-12-08T10:30:00Z",
  "agent": "planner"
}
```

### Compaction

To prevent unbounded growth:

```python
# Keep only last 100 entries in list-based memories
compact_memory_list(base_path, agent_name, "event_log", max_entries=100)

# Archive memories older than 30 days
archive_old_memories(base_path, agent_name, days_old=30)
```

---

## File Structure

```
LeMMing/
├── agents/
│   ├── human/                    # Special human interaction agent
│   │   ├── resume.json
│   │   └── outbox/
│   ├── planner/
│   │   ├── resume.json
│   │   ├── outbox/
│   │   ├── memory/
│   │   ├── workspace/
│   │   └── logs/
│   └── analyst/
│       └── ...
├── config/
│   ├── models.json               # LLM model registry
│   ├── org.json                  # Org-wide settings
│   └── credits.json              # Credit allocations
├── logs/
│   └── engine.log                # Global engine logs
├── shared/                        # Shared workspace (all agents)
├── tick.json                     # Current tick counter
└── lemming/
    ├── engine.py
    ├── agents.py
    ├── messages.py
    ├── memory.py
    ├── tools.py
    ├── providers.py
    ├── logging_config.py
    └── cli.py
```

---

## Extension Points

### Custom Tools

```python
from lemming.tools import Tool, ToolRegistry, ToolResult

class CustomTool(Tool):
    name = "custom_tool"
    description = "Does something custom"

    def execute(self, agent_name: str, base_path: Path, **kwargs) -> ToolResult:
        # Your logic here
        return ToolResult(True, "Success")

ToolRegistry.register(CustomTool())
```

### Custom LLM Provider

```python
from lemming.providers import LLMProvider, register_provider

class CustomProvider(LLMProvider):
    def call(self, model_name, messages, temperature, **kwargs) -> str:
        # Your provider logic
        return response_text

register_provider("custom", CustomProvider)
```

---

## Performance Considerations

1. **Tick Duration**: Minimize LLM latency with fast models or local Ollama
2. **Outbox Cleanup**: Old entries auto-deleted after retention period
3. **Memory Compaction**: Use `compact_memory_list()` for long-running agents
4. **Parallel Execution**: Coming in v2.0 (within-tick parallelism)
5. **Caching**: Consider caching LLM responses for repeated prompts

---

## Security Model

1. **File Access**: Enforced via `file_access` permissions (canonicalized paths)
2. **Shell Tool**: Restricted to agent workspace only
3. **Agent Creation**: `create_agent` tool restricted to `hr` agent
4. **Credit System**: Prevents runaway LLM costs
5. **Circuit Breaker**: Stops cascading failures from provider outages

---

For more guides, see:
- [AGENT_GUIDE.md](./AGENT_GUIDE.md) - Creating and configuring agents
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues and solutions
