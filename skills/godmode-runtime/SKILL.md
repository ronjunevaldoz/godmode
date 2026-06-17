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

### Agent Tiers

| Tier | Agent | Model | Role |
|------|-------|-------|------|
| L2 | `OllamaUtilityAgent` | llama3 (local) | Cheap, repetitive, local-first tasks |
| L2 | `CodexEngineerAgent` | gpt-4o | Implementation-heavy code tasks |
| L2 | `GeminiVisionAgent` | gemini-pro-vision | Multimodal / UI tasks |
| L3 | `ClaudeArchitectAgent` | claude-opus-4-8 | Reasoning, architecture, final validation |

L3 is also the safety-net escalation path when confidence is low or intent is `Architecture.*` / `Review.*`.

## Intent Hierarchy

Intents follow the pattern `Category.Subcategory`:

- `Implementation.*` — Android, KMP, JNI, Backend, DevOps, Web
- `Architecture.*` — System, Mobile, Agent
- `Multimodal.*` — UI, Image
- `Utility.*` — Summary, Classification, Extraction
- `Documentation.*` — Spec, Markdown
- `Review.*` — Code, Architecture
- `UNKNOWN` — Escalates to L3

## Key Files

| File | Purpose |
|------|---------|
| `configs/model_registry.yaml` | Model metadata, capabilities, cost/latency tiers |
| `routing/intent_map.json` | Intent → capability mappings |
| `routing/router.py` | Main routing pipeline |
| `routing/capability_resolver.py` | Intent → capabilities |
| `routing/model_selector.py` | Capability → model scoring |
| `agents/base/agent_base.py` | Abstract base for API-backed agents |

## CLI Commands

```bash
python3 godmode_cli.py run "your prompt"   # Route and execute
python3 godmode_cli.py stats               # Token usage and metrics
python3 godmode_cli.py eval                # Run routing accuracy evaluation
python3 godmode_cli.py clear               # Reset memory
```

## Adding a New Model

1. Add entry to `configs/model_registry.yaml` with `enabled`, `capabilities`, `cost_tier`, `latency_tier`, `privacy`, `context_window`
2. Add corresponding capability mappings to `routing/intent_map.json`
3. Create agent class extending `BaseAgent` (or standalone for local models)
4. Run `python3 godmode_cli.py eval` to verify routing accuracy

## Environment Variables

| Variable | Required By |
|----------|------------|
| `ANTHROPIC_API_KEY` | `ClaudeArchitectAgent` |
| `OPENAI_API_KEY` | `CodexEngineerAgent` |
| `GOOGLE_API_KEY` | `GeminiVisionAgent` |
| `OLLAMA_BASE_URL` | `OllamaUtilityAgent` (defaults to `http://localhost:11434/api/chat`) |
