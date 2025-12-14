---
description: Run the automated agent task background script without requiring manual approval for every command.
---

// turbo-all

1. Start the auto-agent background task
   Running the pre-configured PowerShell script that waits 2 hours then prompts Claude and Codex.
   `Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File .\auto_agent_task.ps1" -WindowStyle Minimized`
