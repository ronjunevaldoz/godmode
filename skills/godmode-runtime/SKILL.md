---
name: godmode-runtime
description: Godmode AI routing runtime — intent hierarchy, agent roles, model registry, and CLI commands for this project
---

# Godmode Runtime

Godmode is a capability-centric AI routing runtime. It classifies intent, resolves required capabilities, and selects the optimal model from a registry — routing to the right specialist automatically.

## Architecture

```
User Prompt → Triage (Ollama/local) → Intent → Capabilities → Model Registry → Agent
```

For full scoring detail see [routing_pipeline.md](references/routing_pipeline.md).

### Agent Tiers

| Tier | Agent | Model | Role |
|------|-------|-------|------|
| L2 | `OllamaUtilityAgent` | qwen2.5-coder:14b (local) | Cheap, repetitive, local-first tasks |
| L2 | `CodexEngineerAgent` | gpt-4o | Implementation-heavy code tasks |
| L2 | `GeminiVisionAgent` | gemini-2.5-pro | Multimodal / UI tasks |
| L3 | `ClaudeArchitectAgent` | claude-opus-4-8 | Reasoning, architecture, final validation |

L3 is also the safety-net escalation path when confidence is low or intent is `Architecture.*` / `Review.*`.

For full agent contracts see [agent_roles.md](references/agent_roles.md).

## Intent Hierarchy

Intents follow `Category.Subcategory`:

- `Implementation.*` — Android, KMP, JNI, Backend, DevOps, Web → `codex_primary`
- `Architecture.*` — System, Mobile, Agent → `claude_architect` (hard-routed)
- `Multimodal.*` — UI, Image → `gemini_vision`
- `Utility.*` — Summary, Classification, Extraction → `ollama_qwen` (local-first)
- `Documentation.*` — Spec, Markdown → `claude_architect`
- `Review.*` — Code, Architecture → `claude_architect` (hard-routed)
- `UNKNOWN` — Escalates to `claude_architect`

## Key Files

| File | Purpose |
|------|---------|
| `configs/model_registry.yaml` | Model metadata, capabilities, cost/latency tiers |
| `routing/intent_map.json` | Intent → capability mappings |
| `routing/router.py` | Main routing pipeline |
| `routing/capability_resolver.py` | Intent → capabilities |
| `routing/model_selector.py` | Capability → model scoring |
| `agents/base/agent_base.py` | Abstract base for API-backed agents |

For model-by-model registry detail see [model_registry.md](references/model_registry.md).

## CLI Commands

```bash
python3 godmode_cli.py run "your prompt"   # Route and execute
python3 godmode_cli.py stats               # Token usage and metrics
python3 godmode_cli.py eval                # Run routing accuracy evaluation
python3 godmode_cli.py clear               # Reset memory
```

## Scripts

Run these before or after sessions to catch config drift early:

```bash
# Pre-flight: validate API keys, Ollama, and config files
python3 skills/godmode-runtime/scripts/health_check.py

# Cross-check registry vs intent map for capability coverage gaps
python3 skills/godmode-runtime/scripts/validate_registry.py

# Run the routing evaluation suite
bash skills/godmode-runtime/scripts/run_eval.sh
```

## Hooks

Hooks run automatically via Claude Code's `settings.json`. Add these to `.claude/settings.json` to make health checks and registry validation part of every session:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 skills/godmode-runtime/scripts/health_check.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 skills/godmode-runtime/scripts/validate_registry.py"
          }
        ]
      }
    ]
  }
}
```

**`PreToolUse` on Bash** — runs `health_check.py` before any shell command; surfaces missing keys or unreachable Ollama before the first `godmode_cli.py run`.

**`PostToolUse` on Edit/Write** — runs `validate_registry.py` whenever `model_registry.yaml` or `intent_map.json` is edited; catches capability drift immediately.

To register hooks without editing JSON manually, use the `update-config` skill.

## Environment Variables

| Variable | Required By |
|----------|------------|
| `ANTHROPIC_API_KEY` | `ClaudeArchitectAgent` |
| `OPENAI_API_KEY` | `CodexEngineerAgent` |
| `GOOGLE_API_KEY` | `GeminiVisionAgent` |
| `OLLAMA_BASE_URL` | `OllamaUtilityAgent` (defaults to `http://localhost:11434/api/chat`) |
