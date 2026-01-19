# LeMMing CLI Management Guide

Welcome, Manager! This guide explains how to manage CLI agents within the LeMMing framework.

## 1. Modular Architecture
LeMMing uses a "Filesystem-First" approach. Agents communicate via outboxes and are defined by `resume.json` files.

## 2. CLI Agents
CLI agents are special agents whose "brain" is a local command instead of an LLM. 
- They receive the prompt as the last argument to their command.
- Their output is captured and wrapped into a LeMMing Message if it's not already JSON.

## 3. Creating a New CLI Agent
To create a new CLI agent (e.g., "git_agent"):
1. **Prepare the model**: Ensure the command you want to run is defined in `lemming/config/models.json`.
   Example model entry:
   ```json
   "cli-git": {
     "provider": "cli",
     "model_name": "git",
     "provider_config": {
       "command": ["git"]
     }
   }
   ```
2. **Create the agent folder**: `agents/git_agent`.
3. **Configure resume.json**:
   ```json
   {
     "name": "git_agent",
     "model": { "key": "cli-git" },
     "permissions": { "read_outboxes": ["manager_cli"] }
   }
   ```
4. **Bootstrap**: Run `python -m lemming.cli bootstrap` to initialize the folders.

## 4. Orchestrating Tasks
As the Manager, you should:
1. Receive a high-level goal from the user (`human`).
2. Break it down into commands for specific CLI agents.
3. Message the CLI agent with the exact command string.
4. Read the CLI agent's outbox in the next tick to see the result.
5. Synthesize the results for the user.

## 5. Security
Agents are restricted to their own `workspace/` and the `shared/` directory. Commands run by CLI agents also inherit these restrictions if the command supports a `cwd`.

Happy managing!
