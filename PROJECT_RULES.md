# PROJECT_RULES

## Architectural Mandates

LeMMing is a filesystem-first multi-agent orchestration framework. These core invariants must be maintained:

### 1. Resume as ABI
- Each agent lives in `agents/<name>/`
- Canonical config is `agents/<name>/resume.json` (NOT `resume.txt`)
- Resume defines: `name`, `title`, `short_description`, `workflow_description`, `instructions`, `model`, `permissions.read_outboxes`, `permissions.tools`, and `schedule.run_every_n_ticks` / `schedule.phase_offset`
- The resume is the complete contract between the framework and the agent

### 2. Outbox-Only Messaging
- Agents never write into other agents' directories
- All communication is via JSON outbox entries in `agents/<agent>/outbox/`
- The canonical message type is `lemming.messages.OutboxEntry`
- Other agents build a virtual inbox by reading permitted outboxes
- Messages are JSON files with timestamp-based filenames

### 3. Tick-Based Scheduler
- Global integer tick counter maintained by the engine
- Agent runs if: `(tick % run_every_n_ticks) == (phase_offset % run_every_n_ticks)`
- `lemming.engine.run_tick` and `run_forever` manage scheduling
- No continuous loops or async event-driven execution within agents
- Deterministic, reproducible execution order

### 4. No Central Org Chart
- Permission graph is derived dynamically from resumes
- `org_chart.json` should NOT exist as authoritative configuration
- Each agent's `permissions.read_outboxes` defines the communication topology
- The org graph is computed on-demand from resume.json files

### 5. Filesystem Transparency
- Everything important is a file: resumes, outboxes, memory, configs, org graph, logs
- Git-trackable and human-readable by default
- No hidden state in databases or binary formats
- Configuration changes are file edits, not API calls

## Implementation Guidelines

### Agent Template
- `agents/agent_template/` is the canonical example
- Use this as the basis for creating new agents
- Contains properly structured `resume.json` and directory layout

### Message Format
- Use `lemming.messages.OutboxEntry` exclusively
- Schema includes: `sender`, `recipient`, `timestamp`, `content`, `importance`, `message_type`
- No direct agent-to-agent file writes outside outbox system

### Engine Design
- Role-agnostic: the engine orchestrates generic agents without hardcoded roles
- Load agents dynamically from `agents/` directory
- Validate resume.json on load
- Respect scheduling constraints from resume.json

### Configuration Files
- `lemming/config/credits.json`: Per-agent credit tracking
- `lemming/config/models.json`: Model provider configurations
- `lemming/config/org_config.json`: Global organization settings
- No `org_chart.json` (computed dynamically from resumes)

## Safety & Constraints

### Error Handling
- Enforce strict handling of LLM JSON outputs
- Never crash on malformed JSON; log issues and continue
- Gracefully handle missing or invalid resume fields
- Validate all configurations on bootstrap and before execution

### Data Safety
- Never delete user data in `agents/` without explicit confirmation
- Preserve agent memory and outbox history
- Log all errors and state changes

### Development Practices
- Avoid adding new dependencies without approval
- Maintain scope focus on core framework features
- Keep solutions simple and filesystem-oriented
- Prefer explicit configuration over implicit behavior

### Testing
- Dynamically create temporary test agents
- Use OutboxEntry system for test message passing
- Never depend on specific demo agents in tests
- Ensure tests clean up temporary files

## Anti-Patterns

❌ **DO NOT:**
- Create central configuration files that duplicate resume.json data
- Implement alternate messaging systems outside OutboxEntry
- Add continuous loops or async event handling within agent execution
- Hardcode agent roles or names in the engine
- Store state outside the filesystem
- Add backwards-compatibility for removed features (messaging.py, file_dispatcher.py, org_chart.json)

✅ **DO:**
- Use `resume.json` as the single source of truth for agent config
- Communicate via OutboxEntry messages in agent outboxes
- Use tick-based scheduling with explicit phase offsets
- Derive the org graph from resume files
- Keep everything in the filesystem
- Reference `agent_template/` as the canonical example
