# Godmode: AI Runtime Orchestration System

## Overview
A capability-centric AI routing runtime that optimizes model selection based on intent, privacy, and cost.

## Key Commands (Skills)
To interact with the system, use the `godmode_cli.py` entry point.

- **Execute Request:** `python3 godmode_cli.py run "your prompt"`
- **View Metrics:** `python3 godmode_cli.py stats`
- **Run Evals:** `python3 godmode_cli.py eval`
- **Reset Memory:** `python3 godmode_cli.py clear`

## Architecture Notes
- **Triage:** Ollama (local)
- **Specialists:** Codex (Code), Gemini (Vision), Claude (Reasoning)
- **Logic:** Intent $\rightarrow$ Capability $\rightarrow$ Model Registry $\rightarrow$ Execution.

## Development Workflow
1. Update `configs/model_registry.yaml` to change model behavior.
2. Update `routing/intent_map.json` to change capability requirements.
3. Run `python3 godmode_cli.py eval` to verify routing accuracy.
4. Use `python3 godmode_cli.py stats` to monitor token efficiency.
