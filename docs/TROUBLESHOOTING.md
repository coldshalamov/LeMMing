# LeMMing Troubleshooting Guide

Common issues and solutions for LeMMing multi-agent systems.

## Table of Contents

1. [Agent Issues](#agent-issues)
2. [Scheduling Issues](#scheduling-issues)
3. [Permission Errors](#permission-errors)
4. [LLM/Provider Issues](#llmprovider-issues)
5. [Memory Issues](#memory-issues)
6. [Performance Issues](#performance-issues)
7. [Debugging Tools](#debugging-tools)

---

## Agent Issues

### Agent Not Running

**Symptom:** Agent doesn't execute during ticks

**Diagnosis:**

```bash
# Check agent configuration
python -m lemming.cli show-agent <agent_name>

# Check schedule
python -m lemming.cli status

# Run validation
python -m lemming.cli validate
```

**Common causes:**

#### 1. Invalid Resume

```bash
# Validation will show specific errors
python -m lemming.cli validate

# Common errors:
# - Missing required fields
# - Invalid JSON syntax
# - Name mismatch between directory and resume.json
```

**Fix:**
- Ensure `resume.json` is valid JSON
- Verify all required fields present
- Check `name` field matches directory name

#### 2. Schedule Misconfigured

```json
{
  "schedule": {
    "run_every_n_ticks": 0,  // ❌ 0 means never run!
    "phase_offset": 0
  }
}
```

**Fix:** Set `run_every_n_ticks` to 1 or higher

#### 3. No Credits

```bash
python -m lemming.cli status
# Shows: agent_name: 0.0 credits left
```

**Fix:** Add credits in `config/credits.json`:

```json
{
  "agents": {
    "agent_name": {
      "max_credits": 1000,
      "current_credits": 1000
    }
  }
}
```

#### 4. Agent Directory Missing

```bash
ls agents/
# agent_name directory doesn't exist
```

**Fix:** Create required directories:

```bash
mkdir -p agents/<agent_name>/outbox
```

---

### Agent Produces No Output

**Symptom:** Agent runs but doesn't write to outbox

**Diagnosis:**

```bash
# Check agent logs
python -m lemming.cli logs <agent_name> --lines 50

# Check memory state
python -m lemming.cli inspect <agent_name>

# Look for outbox entries
ls agents/<agent_name>/outbox/
```

**Common causes:**

#### 1. LLM Returns Empty Response

**Check logs:**
```
LLM output was not valid JSON: ...
```

**Fix:** Review agent instructions - may be too vague or confusing

#### 2. JSON Parse Error

**Check logs:**
```
LLM output was not valid JSON: Expecting ',' delimiter: line 5 column 3
```

**Fix:**
- Improve prompt clarity
- Add JSON format examples to instructions
- Lower temperature for more consistent output

#### 3. Tool Execution Fails

**Check tool results in logs:**
```json
{
  "tool_results": [
    {"success": false, "error": "Access denied to path"}
  ]
}
```

**Fix:** Check file permissions (see [Permission Errors](#permission-errors))

---

### Agent Behavior Unexpected

**Symptom:** Agent does something wrong or unexpected

**Debugging steps:**

1. **Read full conversation history:**

```bash
# Check what messages agent is receiving
python -m lemming.cli inbox --agent <agent_name>

# Check agent memory
python -m lemming.cli inspect <agent_name>
```

2. **Review agent logs:**

```bash
python -m lemming.cli logs <agent_name> --lines 100
```

3. **Test in isolation:**

```bash
# Create test scenario
python -m lemming.cli send <agent_name> "test message"
python -m lemming.cli run-once
python -m lemming.cli inspect <agent_name>
```

4. **Check instructions:**
- Are they specific enough?
- Do they handle edge cases?
- Do they define error handling?

**Common fixes:**
- Clarify instructions
- Add more examples
- Define explicit error handling
- Add memory checkpoints

---

## Scheduling Issues

### Agents Run Out of Order

**Symptom:** Agent B runs before Agent A, but you expected A first

**Understanding intra-tick ordering:**

Agents execute in order: `sorted(agents, key=lambda a: (fire_point(a), a.name))`

Where: `fire_point = ((-phase_offset) mod N) / N`

**Example:**

```json
// Agent A
{"schedule": {"run_every_n_ticks": 4, "phase_offset": 2}}
// fire_point = ((-2) % 4) / 4 = 2/4 = 0.5

// Agent B
{"schedule": {"run_every_n_ticks": 4, "phase_offset": 0}}
// fire_point = ((-0) % 4) / 4 = 0/4 = 0.0

// Execution: B (0.0) runs before A (0.5)
```

**Fix:** Adjust `phase_offset` to control ordering:
- Lower `phase_offset` → runs earlier
- Higher `phase_offset` → runs later

---

### Agent Fires Too Frequently

**Symptom:** Agent runs every tick when it should run less often

**Check:**

```bash
python -m lemming.cli show-agent <agent_name>
# Look at schedule.run_every_n_ticks
```

**Fix:** Increase `run_every_n_ticks`:

```json
{
  "schedule": {
    "run_every_n_ticks": 10,  // Run every 10 ticks
    "phase_offset": 0
  }
}
```

---

### Agent Never Fires

**Symptom:** Agent configured but never executes

**Check firing condition:**

```python
# Agent fires when: (tick + phase_offset) % run_every_n_ticks == 0

# Example:
run_every_n_ticks = 3
phase_offset = 1

tick=0: (0+1) % 3 = 1 ❌
tick=1: (1+1) % 3 = 2 ❌
tick=2: (2+1) % 3 = 0 ✅ FIRES
tick=3: (3+1) % 3 = 1 ❌
tick=4: (4+1) % 3 = 2 ❌
tick=5: (5+1) % 3 = 0 ✅ FIRES
```

**Fix:** Ensure `phase_offset < run_every_n_ticks`

---

## Permission Errors

### Access Denied Errors

**Symptom:**

```
ToolResult(success=False, error="Access denied: read permission denied for ../../../etc/passwd")
```

**Common causes:**

#### 1. Path Not in `allow_read`/`allow_write`

```json
{
  "permissions": {
    "file_access": {
      "allow_read": ["./workspace"],  // Only workspace allowed
      "allow_write": ["./workspace"]
    }
  }
}
```

**Fix:** Add required paths:

```json
{
  "permissions": {
    "file_access": {
      "allow_read": ["./workspace", "./shared", "/data"],
      "allow_write": ["./workspace"]
    }
  }
}
```

#### 2. Path Traversal Attempt

```
file_read path="../../../etc/passwd"
```

**This is blocked by design.** Paths are canonicalized before checking permissions.

**Fix:** Use absolute or proper relative paths within allowed directories.

#### 3. Tool Not Permitted

```bash
# Agent tries to use file_write but doesn't have permission
Tool 'file_write' not permitted for agent_name
```

**Fix:** Add tool to permissions:

```json
{
  "permissions": {
    "tools": ["file_read", "file_write", "memory_write"]
  }
}
```

---

### Cannot Read Other Agent's Outbox

**Symptom:**

```
Agent A cannot see messages from Agent B
```

**Check permissions:**

```bash
python -m lemming.cli show-agent <agent_name>
# Check permissions.read_outboxes
```

**Fix:**

```json
{
  "permissions": {
    "read_outboxes": ["agent_b", "agent_c"],
    // Or use wildcard:
    "read_outboxes": ["*"]
  }
}
```

---

## LLM/Provider Issues

### API Key Not Found

**Symptom:**

```
openai.OpenAIError: The api_key client option must be set
```

**Fix:** Set environment variable:

```bash
export OPENAI_API_KEY="sk-..."
# OR
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Verify:**

```bash
echo $OPENAI_API_KEY
```

---

### Rate Limit Exceeded

**Symptom:**

```
openai.RateLimitError: Rate limit exceeded
```

**Temporary fix:** Wait and retry

**Permanent fix:**

1. **Use retry wrapper:**

```python
from lemming.providers import RetryingLLMProvider, OpenAIProvider, CircuitBreaker

provider = RetryingLLMProvider(
    OpenAIProvider(),
    max_retries=3,
    circuit_breaker=CircuitBreaker(failure_threshold=5, recovery_timeout=60)
)
```

2. **Reduce tick frequency:**

```json
{
  "schedule": {
    "run_every_n_ticks": 5  // Run less often
  }
}
```

3. **Use cheaper models:**

```json
{
  "model": {
    "key": "gpt-4o-mini"  // Instead of gpt-4o
  }
}
```

---

### LLM Timeout

**Symptom:**

```
requests.exceptions.Timeout: HTTPSConnectionPool...
```

**Fix:**

1. **Check network connectivity:**

```bash
ping api.openai.com
```

2. **Increase timeout (for Ollama):**

```python
# In providers.py
response = requests.post(..., timeout=300)  # 5 minutes
```

3. **Use local models:**

```json
{
  "model": {
    "key": "llama3.2:latest",  // Ollama local model
    "provider": "ollama"
  }
}
```

---

### Circuit Breaker Open

**Symptom:**

```
RuntimeError: Circuit breaker is OPEN - too many recent failures
```

**Meaning:** 5+ consecutive LLM failures, system protecting itself

**Fix:**

1. **Check provider health:**

```bash
# For Ollama
curl http://localhost:11434/api/tags

# For OpenAI
curl https://status.openai.com/api/v2/status.json
```

2. **Wait for recovery:**
- Circuit breaker auto-recovers after 60 seconds
- Will attempt one test request (HALF_OPEN)
- If successful, returns to CLOSED (normal)

3. **Reset manually:**

Restart the engine:

```bash
# Stop
^C

# Start fresh
python -m lemming.cli run
```

---

## Memory Issues

### Memory Growing Unbounded

**Symptom:** Agent memory files getting very large

**Check memory size:**

```bash
du -sh agents/*/memory/
```

**Fix: Compact memories:**

```python
from lemming.memory import compact_memory_list

# Keep only last 100 entries
compact_memory_list(base_path, agent_name, "event_log", max_entries=100)
```

**Or use auto-compaction:**

```python
from lemming.memory import append_memory_event

# Automatically compacts to max_entries
append_memory_event(
    base_path,
    agent_name,
    "event_log",
    "Event description",
    max_entries=100  # Auto-compact
)
```

---

### Memory Key Not Found

**Symptom:**

```
ToolResult(success=False, error="Memory not found")
```

**Check:**

```bash
python -m lemming.cli inspect <agent_name>
# Shows all memory keys
```

**Fix:** Initialize memory first:

```json
{
  "memory_updates": [
    {"key": "goals", "value": []}  // Initialize empty list
  ]
}
```

---

### Memory Corruption

**Symptom:**

```
json.JSONDecodeError: Expecting property name enclosed in double quotes
```

**Check file:**

```bash
cat agents/<agent_name>/memory/<key>.json
```

**Fix:**

1. **Restore from backup:**

```bash
cp agents/<agent_name>/memory/archive/<key>.json agents/<agent_name>/memory/<key>.json
```

2. **Or delete and reinitialize:**

```bash
rm agents/<agent_name>/memory/<key>.json
# Agent will recreate on next write
```

---

## Performance Issues

### Slow Tick Execution

**Symptom:** Each tick takes > 10 seconds

**Diagnosis:**

```bash
# Check logs for duration_ms
tail -f logs/engine.log | grep duration_ms
```

**Common causes:**

#### 1. Expensive LLM Calls

**Solution:**
- Use faster models (gpt-4o-mini vs gpt-4o)
- Use local models (Ollama)
- Reduce context length (limit inbox size)

```python
# In messages.py
incoming = collect_readable_outboxes(
    base_path,
    agent.name,
    agent.permissions.read_outboxes,
    limit=10  # Reduce from 30
)
```

#### 2. Too Many Agents Running Per Tick

**Solution:** Spread agents across ticks:

```json
// Agent A
{"schedule": {"run_every_n_ticks": 2, "phase_offset": 0}}

// Agent B
{"schedule": {"run_every_n_ticks": 2, "phase_offset": 1}}

// Now A and B run on alternating ticks
```

#### 3. Shell Tools Timing Out

**Check logs:**

```
Shell execution failed: Command timed out
```

**Solution:**
- Optimize shell commands
- Reduce timeout requirement
- Move heavy processing to separate service

---

### High Memory Usage

**Symptom:** Python process using > 1GB RAM

**Causes:**
- Large agent prompts
- Too many outbox entries in memory
- Large LLM responses

**Solutions:**

1. **Clean up old outbox entries:**

```bash
# Cleanup happens automatically, but you can trigger manually
# Old entries (> 1000 ticks old) are auto-deleted
```

2. **Limit context size:**

```python
# In memory.py
def get_memory_context(base_path, agent_name, max_items=10):  # Reduce from 20
    ...
```

3. **Compact memories:**

```bash
# From Python
from lemming.memory import compact_all_agent_memories
compact_all_agent_memories(base_path, agent_name, max_entries=50)
```

---

## Debugging Tools

### CLI Debugging Commands

```bash
# Validate all configurations
python -m lemming.cli validate

# Check agent configuration
python -m lemming.cli show-agent <agent_name>

# View agent state
python -m lemming.cli inspect <agent_name>

# Read logs
python -m lemming.cli logs <agent_name> --lines 100

# Check system status
python -m lemming.cli status

# List all agents
python -m lemming.cli list-agents

# View organization graph
python -m lemming.cli derive-graph
```

### Manual Inspection

```bash
# Check current tick
cat tick.json

# View agent outbox
ls -lh agents/<agent_name>/outbox/
cat agents/<agent_name>/outbox/00000042_*.json | jq

# View agent memory
ls agents/<agent_name>/memory/
cat agents/<agent_name>/memory/goals.json | jq

# Check agent logs
tail -f agents/<agent_name>/logs/activity.log

# Check engine logs
tail -f logs/engine.log | jq
```

### Interactive Testing

```bash
# Send test message
python -m lemming.cli send <agent_name> "test input"

# Run single tick
python -m lemming.cli run-once

# Check results
python -m lemming.cli inspect <agent_name>

# Interactive chat
python -m lemming.cli chat --agent <agent_name>
```

### Python Debugging

```python
# In Python REPL
from pathlib import Path
from lemming.agents import discover_agents, load_agent
from lemming.engine import run_tick
from lemming.messages import read_outbox_entries

base_path = Path(".")

# Load agent
agent = load_agent(base_path, "planner")
print(agent)

# Check schedule
from lemming.engine import should_run
print(should_run(agent, tick=10))

# Read outbox
entries = read_outbox_entries(base_path, "planner", limit=5)
for entry in entries:
    print(entry.payload)

# Run single tick with debugging
import logging
logging.basicConfig(level=logging.DEBUG)
results = run_tick(base_path, tick=1)
print(results)
```

---

## Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `Agent '<name>' not found` | Missing resume.json | Create resume.json in agents/<name>/ |
| `Tool '<tool>' not permitted` | Tool not in permissions | Add tool to permissions.tools |
| `Access denied to path` | File outside allowed paths | Add path to file_access.allow_read/write |
| `Agent has no credits` | Credits exhausted | Add credits in config/credits.json |
| `LLM output was not valid JSON` | Malformed LLM response | Improve instructions, lower temperature |
| `Circuit breaker is OPEN` | Too many LLM failures | Wait 60s for recovery, check provider |
| `Missing required field` | Invalid resume.json | Add missing field to resume |
| `Command timed out` | Shell tool timeout | Optimize command or increase timeout |
| `Memory not found` | Key doesn't exist | Initialize memory key first |

---

## Getting Help

If you can't resolve an issue:

1. **Check logs:**
   ```bash
   python -m lemming.cli logs <agent_name> --lines 100
   tail -f logs/engine.log | jq
   ```

2. **Validate configuration:**
   ```bash
   python -m lemming.cli validate
   ```

3. **Test in isolation:**
   ```bash
   python -m lemming.cli chat --agent <agent_name>
   ```

4. **File an issue:**
   - Include: resume.json, logs, error message
   - Describe: expected vs actual behavior
   - Repository: https://github.com/coldshalamov/LeMMing

---

## Related Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System internals
- [AGENT_GUIDE.md](./AGENT_GUIDE.md) - Creating agents
- [README.md](../README.md) - Getting started
