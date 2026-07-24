# CLI Agent & Modular Manager Specification

## Overview
This document outlines the architecture for extending LeMMing to support **CLI-based Agents** and a **Hierarchical Manager** system. This allows users to wrap existing CLI tools (OpenCode, GitHub Copilot CLI, custom scripts) as autonomous agents within the LeMMing organization, controlled by a manager agent.

## 1. CLI Agent Architecture

The core idea is to allow an agent's "brain" to be a running CLI process or command instead of an API-based LLM call.

### 1.1 New Provider: `CLIProvider`
We will introduce a new provider in `lemming/providers.py` that interfaces with local processes.

**Modes:**
1.  **Stateless (Command Mode)**: Runs a command for each "turn", passing the prompt as an argument or stdin.
    *   *Usage*: Tools that give a single answer and exit (e.g., `gh copilot explain`).
2.  **Stateful (Shell Mode)**: Maintains a persistent process (like a subprocess or PTY) and writes to stdin/reads from stdout.
    *   *Usage*: Interactive REPLs, `opencode` (if interactive), custom agent loops.

### 1.2 Configuration (`resume.json`)
We extend `resume.json` to support CLI configuration.

```json
{
  "name": "code_cli",
  "model": {
    "provider": "cli",
    "model_name": "opencode",
    "provider_config": {
      "command": ["opencode", "--interactive"],
      "mode": "stateful",
      "cwd": "${workspace}",
      "env": {
        "OPENAI_API_KEY": "${env.OPENAI_API_KEY}"
      },
      "timeout": 60
    }
  },
  "instructions": "You are a CLI wrapper. Output is ignored as instructions."
}
```

### 1.3 Adapting Output (The JSON Problem)
LeMMing expects agents to output well-formed JSON (`OutboxEntry`). CLI tools typically output raw text.
To bridge this gap, the `CLIProvider` will automatically wrap raw text output into a valid LeMMing response structure *unless* the CLI is specifically designed to output LeMMing JSON.

**Wrapper Logic:**
```python
# Pseudo-code for CLIProvider wrapper
output = process.read_output()
try:
    return json.loads(output) # specific CLI agents might speak JSON
except JSONDecodeError:
    # Wrap raw text
    return json.dumps({
        "outbox_entries": [
            {
                "kind": "message",
                "payload": {"text": output},
                "tags": ["cli_output"]
            }
        ]
    })
```

## 2. Modular Manager Agent

A new "Manager" agent will be designed to coordinate these CLI workers.

### 2.1 Responsibilities
1.  **Prompt Queuing**: The manager decides which prompts/jobs to send to which CLI agent.
2.  **Output Synthesis**: Reads the raw text output from CLI agents and synthesizes it for the user or other agents.
3.  **Configuration**: Can help the user generate `resume.json` files for new CLI agents via a conversation.

### 2.2 Workflow
1.  User talks to **Manager**.
2.  Manager decides: "I need to ask the generic coder."
3.  Manager writes to `code_cli`'s outbox (or purely queues it if `code_cli` is just a tool).
    *   *Correction*: In LeMMing, agents read *other* agents' outboxes.
    *   So Manager writes a request targeted at `code_cli`.
4.  `code_cli` runs (on its tick), sees the message (via input history), and its "model" (the CLI process) processes it.
5.  `code_cli` outputs raw text, which is wrapped as a message.
6.  Manager reads `code_cli`'s output, parses it, and continues.

## 3. Implementation Plan

### Phase 1: Core CLI support
1.  Implement `CLIProvider` in `lemming/providers.py`.
2.  Add logic to handle `subprocess` execution.
3.  Implement the "Raw Text -> JSON" wrapper.

### Phase 2: Resume & Config Updates
1.  Update `lemming/models.py` to allow `cli` provider type.
2.  Update validation logic.

### Phase 3: The Manager
1.  Create `agents/manager_cli/resume.json`.
2.  Give it instructions to oversee CLI agents.

## 4. Security
Running arbitrary CLI commands is dangerous.
*   **Sandboxing**: CLI agents should default to running in their `workspace` directory.
*   **Allowlist**: Initially, maybe only allow specific commands or warn heavily on bootstrapping.
