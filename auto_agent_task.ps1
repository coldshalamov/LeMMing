<#
.SYNOPSIS
    Automated Agent Workflow Script
    Waits for 2 hours, then triggers Claude Code followed by Codex on the repo.

.DESCRIPTION
    This script is designed to run in the background.
    1. Waits 7200 seconds (2 hours).
    2. Invokes Claude Code (cli) with a prompt.
    3. Invokes Codex (cli) with a prompt.
#>

param(
    [int]$DelaySeconds = 7200
)

# Configuration
$ClaudePath = "$env:APPDATA\npm\claude.cmd"
$CodexPath = "$env:APPDATA\npm\codex.cmd"
$RepoPath = "c:\Users\User\Documents\GitHub\Telomere\LeMMing"

# Define the prompts
$PromptForClaude = "Analyze the codebase in the current directory. Create a file named 'AUTO_ANALYSIS.md' summarizing the project structure and identifying key components."
$PromptForCodex = "Read the 'AUTO_ANALYSIS.md' file. Append a section 'SUGGESTED IMPROVEMENTS' with 3 specific code improvement ideas."

Start-Transcript -Path "$RepoPath\agent_workflow_log.txt" -Append

Write-Host "Started Agent Workflow at $(Get-Date)"
Write-Host "Waiting for $DelaySeconds seconds (2 hours)..."

# Wait
Start-Sleep -Seconds $DelaySeconds

Write-Host "Timer complete. Switching to Repo: $RepoPath"
Set-Location $RepoPath

# ---------------------------------------------------------
# STEP 1: CLAUDE CODE
# ---------------------------------------------------------
Write-Host "Invoking Claude Code..."

# We construct an input block to handle potential interactive prompts.
# 1. '1' handles the 'Do you trust this folder?' prompt if it appears.
# 2. The actual prompt.
# 3. '/exit' to ensure it closes if it enters a REPL loop.
$ClaudeInput = "1`n$PromptForClaude`n/exit`n"

try {
    # Pipe input to Claude
    $ClaudeInput | & $ClaudePath
    Write-Host "Claude Code invocation complete."
} catch {
    Write-Error "Failed to run Claude Code: $_"
}

# Short pause between agents
Start-Sleep -Seconds 10

# ---------------------------------------------------------
# STEP 2: CODEX CLI
# ---------------------------------------------------------
Write-Host "Invoking Codex CLI..."

# Codex input handling (assuming similar stdin acceptance)
$CodexInput = "$PromptForCodex`n"

try {
    $CodexInput | & $CodexPath
    Write-Host "Codex CLI invocation complete."
} catch {
    Write-Error "Failed to run Codex CLI: $_"
}

Write-Host "Workflow finished at $(Get-Date)"
Stop-Transcript
