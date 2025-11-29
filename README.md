
# 🧠 LeMMing: Lightweight Multi-Agent Management Interface

> **LeMMing** – "Lightweight Multi-Agent Management Interface" – is a fully modular system that lets you create, manage, and orchestrate intelligent agents like a digital organization of AI workers. Built for humans and LLMs alike to coordinate scalable, explainable, and persistent workflows.

---

## 🔧 What is LeMMing?

LeMMing is a UI-driven framework that lets you **spawn, instruct, and connect multiple LLM agents**, each with a defined role, access scope, and memory. Inspired by real-world org structures (manager, HR, workers, planners, etc), it allows you to construct a **persistent, distributed multi-agent system** that can manage complex tasks without supervision.

It offers:
- Persistent memory via filesystem-based "agent folders"
- Role-based messaging via permissioned agent-to-agent communication
- Scriptable control of tools, instructions, and context
- Credit and speed budget controls per agent or org
- Self-expanding orgs via HR agents and spawn permissions
- Flexible interface to multiple LLM providers and models

---

## 📘 Vision

Imagine hiring a team of AI specialists. Some summarize. Some code. Some debug. Others plan or organize context. LeMMing lets you:
- Think like a **CEO** of your own digital AI company.
- Manage a hierarchy of agents that pass work, track context, avoid repetition, and build things together.
- Stay focused on **goals**, not syntax or prompting.

---

## 🧱 System Overview

```
           +----------------+
           |     YOU        |
           +--------+-------+
                    |
                [Manager]
                    |
     +--------------+--------------+
     |                             |
 [HR Agent]                  [Context Tracker]
     |                             |
 [Worker Agents] <-> [Read/Write Agent] <-> [File System]
```

---

## 📂 File System Structure

Each agent has a persistent folder like:

```
agents/
└── agent_name/
    ├── instructions.txt
    ├── permissions.json
    ├── inbox/
    ├── outbox/
    ├── memory/
    └── logs/
```

Global config:

```
org_config/
├── org_chart.json
├── model_registry.json
└── budget_limits.json
```

---

## ⚙️ Agent Components

- **Instructions:** Core system prompt that defines its purpose.
- **Permissions:** What agents it can read/write to.
- **Inbox/Outbox:** Messaging queues simulated via folders.
- **Memory:** Persistent context store (summaries, states).
- **Logs:** Audit trail of actions taken.

---

## 📨 Messaging System

Agents communicate by **writing messages to each other's outboxes**.

Each message is a `.txt` file with:
- Timestamp
- Target agent
- Message content
- Optional priority/urgency tag

A read/write script (Python or Codex) routes messages per the `org_chart`.

---

## 🧠 Sample Agent Resumes (Roles)

```json
{
  "name": "error_tracker",
  "model": "gpt-4",
  "instructions": "Log and summarize code errors passed to you. Categorize by root cause.",
  "permissions": {
    "read_from": ["coder_agent"],
    "write_to": ["manager"]
  }
}
```

---

## 🛠️ Initial Agent Types

| Role             | Purpose                                               |
|------------------|-------------------------------------------------------|
| Manager          | Talks to user, routes goals to other agents           |
| Read/Write Agent | Manages filesystem actions (write files, move data)   |
| HR Agent         | Spawns new agents based on resource bottlenecks       |
| Error Tracker    | Logs and summarizes crashes or issues in code         |
| Planner          | Plans steps required to complete user goal            |
| Optimizer        | Refactors prompts or code before execution            |
| Summarizer       | Condenses files or histories into smaller formats     |
| Org Analyzer     | Monitors message bottlenecks, proposes speed changes  |

---

## 🔄 Execution Cycle

LeMMing operates in **turns**:

- Every X minutes (org speed), each agent:
  - Checks inbox
  - Processes messages
  - Writes to outboxes (other agents)
  - Optionally alters its memory/logs
- All messaging is governed by a **central permission table** (`org_chart.json`).

---

## 💰 Budgeting & Speed

- Each model has a **credit cost per turn**.
- You can configure:
  - Global org speed (turn interval)
  - Agent-specific multipliers (e.g. HR agent runs every 3 turns)
  - Daily caps
- The system tracks **costs and credits** in `budget_limits.json`.

---

## 🚀 Example Use Case: Debug a Python Script

1. User tells Manager: "Fix this Python script that crashes on line 22."
2. Manager delegates to Planner → Error Tracker → Coder
3. Each agent does its task, sends message to the next
4. Read/Write agent edits the file based on coder's changes
5. Error Tracker logs outcome and forwards to Manager
6. Manager tells user what was done and why

---

## 🌐 API Integration (Future)

- Plug-in OpenAI, Claude, Gemini, Mistral APIs
- Set quotas and models in `model_registry.json`
- Each agent can use any model with defined cost

---

## 🧪 Getting Started

**Requirements**: Python 3.9+, basic CLI

```bash
git clone https://github.com/yourname/lemming
cd lemming
pip install -r requirements.txt
python main.py
```

---

## 📈 Roadmap

- [x] Local agent simulation
- [ ] VS Code extension for visualization
- [ ] Web dashboard
- [ ] API integration (multi-model support)
- [ ] Marketplace for resumes and org templates


---

## 🧙‍♂️ Inspired by

- LangGraph, CrewAI, BabyAGI, Zapier
- Human organizational psychology
- Personal AI productivity stacks

---

*Build your own company of bots.* 🧱💼

"""

Markdown(readme_content)
