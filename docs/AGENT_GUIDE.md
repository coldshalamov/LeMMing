# LeMMing Agent Development Guide

Complete guide to creating, configuring, and managing LeMMing agents.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Resume Schema](#resume-schema)
3. [Scheduling](#scheduling)
4. [Permissions](#permissions)
5. [Writing Instructions](#writing-instructions)
6. [Tool Usage](#tool-usage)
7. [Memory Management](#memory-management)
8. [Best Practices](#best-practices)
9. [Examples](#examples)

---

## Quick Start

### Create a New Agent

```bash
# 1. Create agent directory
mkdir -p agents/my_agent/outbox

# 2. Create resume.json
cat > agents/my_agent/resume.json <<'EOF'
{
  "name": "my_agent",
  "title": "My Custom Agent",
  "short_description": "Does amazing things",
  "workflow_description": "Monitors X, processes Y, reports to Z",
  "model": {
    "key": "gpt-4o-mini",
    "temperature": 0.2,
    "max_tokens": 2048
  },
  "permissions": {
    "read_outboxes": ["*"],
    "tools": ["file_read", "memory_write"]
  },
  "schedule": {
    "run_every_n_ticks": 1,
    "phase_offset": 0
  },
  "instructions": "You are a helpful assistant...",
  "credits": {
    "max_credits": 1000,
    "soft_cap": 500
  }
}
EOF

# 3. Test the agent
python -m lemming.cli validate
python -m lemming.cli show-agent my_agent
python -m lemming.cli run-once
```

---

## Resume Schema

### Complete Schema Reference

```json
{
  "name": "agent_name",                      // REQUIRED: Must match directory name
  "title": "Human Readable Title",           // REQUIRED
  "short_description": "Brief summary",      // REQUIRED
  "workflow_description": "Detailed flow",   // Optional

  "model": {                                 // REQUIRED
    "key": "gpt-4o-mini",                   // Model ID (see config/models.json)
    "temperature": 0.2,                     // 0.0 = deterministic, 1.0 = creative
    "max_tokens": 2048                      // Response length limit
  },

  "permissions": {                           // REQUIRED
    "read_outboxes": ["agent1", "agent2", "*"],  // Which agents' messages to read
    "tools": ["file_read", "memory_write"]      // Which tools this agent can use
  },

  "schedule": {                              // REQUIRED
    "run_every_n_ticks": 1,                 // Fire every N ticks (1 = every tick)
    "phase_offset": 0                       // Offset for intra-tick ordering
  },

  "instructions": "You are...",              // REQUIRED: Agent system prompt

  "credits": {                               // REQUIRED
    "max_credits": 1000,                    // Maximum credit allocation
    "soft_cap": 500                         // Warning threshold
  }
}
```

### Field Descriptions

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | - | **REQUIRED.** Agent identifier. Must match directory name. |
| `title` | string | - | **REQUIRED.** Human-readable name for UI display. |
| `short_description` | string | - | **REQUIRED.** One-line summary of agent purpose. |
| `workflow_description` | string | "" | Optional detailed workflow explanation. |
| `model.key` | string | "gpt-4o-mini" | LLM model identifier (from `config/models.json`). |
| `model.temperature` | float | 0.2 | Sampling temperature (0.0-1.0). |
| `model.max_tokens` | int | 2048 | Maximum response tokens. |
| `permissions.read_outboxes` | array | [] | Agent names whose outboxes this agent can read. Use `"*"` for all. |
| `permissions.tools` | array | [] | List of tool names this agent can execute. |
| File sandbox | derived | `workspace/`, `shared/` | File tools are restricted to the agent workspace plus shared directory. |
| `schedule.run_every_n_ticks` | int | 1 | Agent fires every N ticks. Use 0 to disable auto-run. |
| `schedule.phase_offset` | int | 0 | Offset for intra-tick ordering (0 to N-1). |
| `instructions` | string | "" | **REQUIRED.** System prompt defining agent behavior. |
| `credits.max_credits` | float | 1000 | Maximum credit allocation for this agent. |
| `credits.soft_cap` | float | 500 | Warning threshold for credit usage. |

---

## Scheduling

### Basic Scheduling

```json
{
  "schedule": {
    "run_every_n_ticks": 1,  // Run every tick
    "phase_offset": 0
  }
}
```

**Common patterns:**

| Pattern | `run_every_n_ticks` | Use Case |
|---------|---------------------|----------|
| **Always on** | 1 | Coordinators, monitors, high-priority agents |
| **Periodic** | 5 | Regular check-ins, status reports |
| **Slow** | 10+ | Background tasks, summarization, archiving |
| **Disabled** | 0 | Human agent, manually triggered agents |

### Advanced Scheduling: Phase Offsets

Control **when** agents run within a multi-agent system:

```python
# Firing condition: (tick + phase_offset) % run_every_n_ticks == 0

# Example: 3 agents, all run_every_n_ticks=3
Agent A: phase_offset=0 → fires at ticks 0, 3, 6, 9, ...
Agent B: phase_offset=1 → fires at ticks 2, 5, 8, 11, ...
Agent C: phase_offset=2 → fires at ticks 1, 4, 7, 10, ...
```

**Use cases:**
- **Pipeline stages**: Data fetcher (offset=0) → Processor (offset=1) → Reporter (offset=2)
- **Load distribution**: Spread agent execution across ticks
- **Ordered dependencies**: Ensure A completes before B

### Intra-Tick Ordering

If multiple agents fire in the same tick, they execute in **deterministic order**:

1. Compute `fire_point = ((-phase_offset) mod N) / N`
2. Sort by `(fire_point, agent_name)` ascending

**Example:**
```
Agents firing at tick 4:
- planner (N=1, offset=0) → fire_point = 0.0
- analyst (N=4, offset=3) → fire_point = 0.25
- reporter (N=2, offset=0) → fire_point = 0.0

Execution order: planner (0.0, "planner"), reporter (0.0, "reporter"), analyst (0.25, "analyst")
```

---

## Permissions

### Read Permissions

Control which agents' outboxes this agent can read:

```json
{
  "permissions": {
    "read_outboxes": ["planner", "analyst", "coordinator"]
  }
}
```

**Wildcard:** Use `"*"` to read all outboxes:

```json
{
  "permissions": {
    "read_outboxes": ["*"]
  }
}
```

### Tool Permissions

Agents must explicitly request tool access:

```json
{
  "permissions": {
    "tools": [
      "file_read",
      "file_write",
      "file_list",
      "memory_read",
      "memory_write",
      "shell",
      "list_agents"
    ]
  }
}
```

**Available tools:**

| Tool | Description | Permission Requirements |
|------|-------------|-------------------------|
| `file_read` | Read files | Workspace/shared sandbox |
| `file_write` | Write files | Workspace/shared sandbox |
| `file_list` | List directory contents | Workspace/shared sandbox |
| `shell` | Execute shell commands | Workspace only |
| `memory_read` | Load memory entries | Always allowed |
| `memory_write` | Save memory entries | Always allowed |
| `create_agent` | Spawn new agents | Restricted to `hr` agent |
| `list_agents` | List all agents | Always allowed |

### File Access Permissions

File tools are automatically sandboxed to `agents/<name>/workspace/` plus the shared directory. Paths are canonicalized (symlinks resolved) before permission checks, and attempts to access anything outside the sandbox are denied.
- Attempting to access unauthorized paths returns an error

---

## Writing Instructions

The `instructions` field is the agent's **system prompt** - the most important part of agent design.

### Structure

```
You are a [ROLE].

Your responsibilities:
- [Responsibility 1]
- [Responsibility 2]

You have access to:
- [Tool 1]: Used for [purpose]
- [Tool 2]: Used for [purpose]

Workflow:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Communication:
- Send messages to [agent names] for [purpose]
- Read messages from [agent names] for [purpose]

Remember:
- [Key constraint or behavior]
- [Important guideline]
```

### Example: Data Analyst Agent

```json
{
  "instructions": "You are a data analyst agent responsible for processing and analyzing datasets.

Your responsibilities:
- Monitor the shared/data/ directory for new CSV files
- Analyze data using statistical methods
- Generate summary reports
- Alert the coordinator if anomalies are detected

You have access to:
- file_read: Read CSV files from shared/data/
- file_write: Write analysis reports to your workspace
- memory_write: Store analysis history
- shell: Run data processing scripts (pandas, numpy)

Workflow:
1. Check for new files in shared/data/ using file_list
2. Read and validate CSV structure
3. Perform statistical analysis (mean, median, outliers)
4. Generate summary report in Markdown
5. If anomalies found, send urgent message to coordinator
6. Save analysis history to memory

Communication:
- Send reports to: coordinator, reporter
- Read instructions from: planner, human

Remember:
- Always validate data before analysis
- Log all errors to memory for debugging
- Keep reports concise and actionable
- Never modify source data files"
}
```

### Best Practices for Instructions

✅ **DO:**
- Be specific about responsibilities
- List available tools and their purposes
- Define clear workflows
- Specify communication patterns
- Include error handling guidance

❌ **DON'T:**
- Write vague instructions like "You're a helpful assistant"
- Forget to mention available tools
- Leave communication patterns undefined
- Omit constraints and guardrails

---

## Tool Usage

### Using Tools in Agent Responses

Agents use tools by including `tool_calls` in their JSON response:

```json
{
  "outbox_entries": [],
  "tool_calls": [
    {
      "tool": "file_read",
      "args": {"path": "data.csv"}
    },
    {
      "tool": "memory_write",
      "args": {"key": "last_analysis", "value": {"date": "2025-12-08", "status": "complete"}}
    }
  ],
  "memory_updates": [],
  "notes": "Read data file and saved analysis status"
}
```

### Tool Reference

#### file_read

```json
{
  "tool": "file_read",
  "args": {"path": "workspace/data.txt"}
}
```

**Returns:** File contents as string

#### file_write

```json
{
  "tool": "file_write",
  "args": {
    "path": "workspace/report.md",
    "content": "# Analysis Report\n\n..."
  }
}
```

**Returns:** Success message

#### file_list

```json
{
  "tool": "file_list",
  "args": {"path": "shared/data"}
}
```

**Returns:** Newline-separated list of file names

#### shell

```json
{
  "tool": "shell",
  "args": {"command": "python analyze.py"}
}
```

**Returns:** stdout + stderr (30s timeout)

#### memory_read

```json
{
  "tool": "memory_read",
  "args": {"key": "goals"}
}
```

**Returns:** JSON value stored at key

#### memory_write

```json
{
  "tool": "memory_write",
  "args": {"key": "goals", "value": ["goal1", "goal2"]}
}
```

**Returns:** Success message

---

## Memory Management

### Memory Keys

Organize memory with meaningful keys:

```
context         - Current operational context
goals           - Short-term goals
facts           - Persistent facts learned
event_log       - Timestamped events
preferences     - User preferences
```

### Saving Memory

Direct save via tool:

```json
{
  "tool": "memory_write",
  "args": {"key": "goals", "value": ["Analyze Q4", "Prepare report"]}
}
```

Or via `memory_updates` (shorthand):

```json
{
  "memory_updates": [
    {"key": "context", "value": {"task": "analyzing", "file": "data.csv"}}
  ]
}
```

### Memory Compaction

For long-running agents, compact memories to prevent unbounded growth:

```python
from lemming.memory import compact_memory_list, archive_old_memories

# Keep only last 100 entries in event log
compact_memory_list(base_path, "analyst", "event_log", max_entries=100)

# Archive memories older than 30 days
archive_old_memories(base_path, "analyst", days_old=30)
```

---

## Best Practices

### 1. Single Responsibility

Each agent should have **one clear purpose**:

✅ Good:
- `data_fetcher` - Fetches data from API
- `data_analyzer` - Analyzes fetched data
- `report_generator` - Generates reports from analysis

❌ Bad:
- `data_everything` - Fetches, analyzes, and reports

### 2. Explicit Communication

Define clear communication patterns:

```json
{
  "instructions": "...

  Communication:
  - Send analysis results to: reporter
  - Send errors to: coordinator
  - Read tasks from: planner, human
  - Never send messages to: data_fetcher
  ..."
}
```

### 3. Error Handling

Always include error handling guidance:

```
If file read fails:
1. Log error to memory
2. Send error message to coordinator
3. Mark task as failed in notes

Never crash silently.
```

### 4. Idempotency

Design agents to be **idempotent** - safe to run multiple times:

```
Before processing file X:
1. Check if already processed (via memory)
2. If yes, skip processing
3. If no, process and mark as done
```

### 5. Credit Management

Monitor credit usage:

```json
{
  "credits": {
    "max_credits": 1000,   // Agent stops when exhausted
    "soft_cap": 800        // Warning threshold
  }
}
```

Check credit status:

```bash
python -m lemming.cli status
```

### 6. Testing

Test agents incrementally:

```bash
# 1. Validate resume
python -m lemming.cli validate

# 2. Inspect agent config
python -m lemming.cli show-agent my_agent

# 3. Run single tick
python -m lemming.cli run-once

# 4. Check agent output
python -m lemming.cli inspect my_agent

# 5. View logs
python -m lemming.cli logs my_agent --lines 50
```

---

## Examples

### Example 1: Monitor Agent

```json
{
  "name": "monitor",
  "title": "System Monitor",
  "short_description": "Monitors system health and alerts on issues",
  "model": {"key": "gpt-4o-mini", "temperature": 0.1},
  "permissions": {
    "read_outboxes": ["*"],
    "tools": ["shell", "memory_write", "memory_read"]
  },
  "schedule": {"run_every_n_ticks": 5, "phase_offset": 0},
  "instructions": "You are a system monitor.

Every 5 ticks:
1. Check disk usage: `df -h`
2. Check memory: `free -h`
3. Compare to previous values (from memory)
4. If usage > 80%, send urgent message to human
5. Update memory with current values

Format messages as:
{\"kind\": \"status\", \"payload\": {\"metric\": \"disk\", \"value\": \"85%\", \"threshold\": \"80%\"}}",
  "credits": {"max_credits": 500, "soft_cap": 250}
}
```

### Example 2: Coordinator Agent

```json
{
  "name": "coordinator",
  "title": "Task Coordinator",
  "short_description": "Coordinates work between specialized agents",
  "model": {"key": "gpt-4o", "temperature": 0.3},
  "permissions": {
    "read_outboxes": ["*"],
    "tools": ["memory_write", "memory_read", "list_agents"]
  },
  "schedule": {"run_every_n_ticks": 1, "phase_offset": 0},
  "instructions": "You are the coordinator agent.

Responsibilities:
- Read incoming requests from human agent
- Break down complex tasks into subtasks
- Assign subtasks to appropriate specialist agents
- Track task progress in memory
- Report completion to human

Workflow:
1. Check inbox for new requests (kind='request')
2. Analyze request and identify required agents
3. Send task messages to specialist agents
4. Monitor responses (kind='response')
5. When all complete, send completion report to human

Memory structure:
{
  \"active_tasks\": [{\"id\": \"...\", \"status\": \"in_progress\", \"assigned_to\": \"...\"}],
  \"completed_tasks\": [...]
}",
  "credits": {"max_credits": 2000, "soft_cap": 1500}
}
```

### Example 3: Research Agent

```json
{
  "name": "researcher",
  "title": "Research Specialist",
  "short_description": "Gathers information from files and web",
  "model": {"key": "gpt-4o-mini", "temperature": 0.5},
  "permissions": {
    "read_outboxes": ["coordinator", "human"],
    "tools": ["file_read", "file_list", "memory_write", "shell"]
  },
  "schedule": {"run_every_n_ticks": 2, "phase_offset": 1},
  "instructions": "You are a research specialist agent.

When you receive a research request:
1. Identify information sources (files in ./data/, web APIs)
2. Gather relevant information using file_read
3. Synthesize findings into a structured report
4. Save report to workspace/research_<topic>.md
5. Send report summary to requester

Output format:
# Research Report: [Topic]

## Summary
Brief overview...

## Findings
- Finding 1
- Finding 2

## Sources
- source1.txt
- source2.csv

Remember:
- Cite all sources
- Save intermediate results to memory
- If sources unavailable, report back immediately",
  "credits": {"max_credits": 1500, "soft_cap": 1000}
}
```

---

## CLI Reference

```bash
# Create and validate agent
python -m lemming.cli validate
python -m lemming.cli show-agent <name>

# Run agent
python -m lemming.cli run-once
python -m lemming.cli run

# Inspect agent state
python -m lemming.cli inspect <name>
python -m lemming.cli logs <name> --lines 50

# Human interaction
python -m lemming.cli send <agent> "message"
python -m lemming.cli inbox
python -m lemming.cli chat --agent <name>

# System status
python -m lemming.cli status
python -m lemming.cli list-agents
```

---

## Next Steps

- Read [ARCHITECTURE.md](./ARCHITECTURE.md) for system internals
- Read [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for debugging help
- Check `agents/example_planner/` for a complete example
