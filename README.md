# Godmode

**Local-first AI routing runtime.** Classifies your prompt's intent, picks the right model from a registry, and runs it — preferring free local (Ollama) models over paid cloud APIs. Shows you exactly how much you saved.

```
Your prompt → Triage (Ollama) → Intent → Capabilities → Model Registry → Agent → Result
```

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install and start Ollama  →  https://ollama.com/download
#    Pull at least one model:
ollama pull qwen3:8b

# 3. Run the setup wizard (configures your Ollama URL and assigns models to roles)
python3 godmode_cli.py setup

# 4. Run your first prompt
python3 godmode_cli.py run "Summarise the key ideas behind clean architecture"

# 5. See your savings
python3 godmode_cli.py stats
```

---

## Operating Modes

| Mode | Set via | Behaviour |
|------|---------|-----------|
| `skill` *(default)* | `GODMODE_MODE=skill` | Runs inside Claude Desktop. No cloud keys needed. High-stakes results are flagged `NEEDS REVIEW` instead of escalating to a paid API. |
| `standalone` | `GODMODE_MODE=standalone` | Runs independently. Low-quality or high-stakes results auto-escalate to cloud models (requires API keys). |

---

## All Commands

```bash
python3 godmode_cli.py setup              # First-run wizard — configure Ollama + assign models
python3 godmode_cli.py run "prompt"       # Route and execute a prompt
python3 godmode_cli.py stats              # Token savings dashboard + verdict
python3 godmode_cli.py models             # List pulled Ollama models and their assigned roles
python3 godmode_cli.py preset list        # Show RAM-tiered model preset matrix
python3 godmode_cli.py preset apply auto  # Auto-select and apply the best preset for your server
python3 godmode_cli.py recommend          # Score all pulled models and suggest registry changes
python3 godmode_cli.py recommend --apply  # Apply those suggestions
python3 godmode_cli.py eval               # Run routing accuracy evaluation (11 test cases)
python3 godmode_cli.py clear              # Reset task memory / logs
python3 godmode_cli.py coverage           # Run test suite with line coverage report
```

---

## Configuration

All config lives in plain files — no UI required.

| File | Purpose |
|------|---------|
| `.env.local` | Your personal env vars (gitignored). Created by `setup`. |
| `.env.example` | Template — copy to `.env.local` and fill in. |
| `configs/model_registry.yaml` | Model metadata, capabilities, cost rates. |
| `routing/intent_map.json` | Intent → capability mappings. |

### Environment Variables

| Variable | Default | Required |
|----------|---------|----------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | For Ollama routing |
| `OLLAMA_SERVER_RAM_GB` | auto-detected | Improves preset recommendations |
| `GODMODE_MODE` | `skill` | `skill` or `standalone` |
| `ANTHROPIC_API_KEY` | — | Only in `standalone` mode |
| `OPENAI_API_KEY` | — | Only in `standalone` mode |
| `GOOGLE_API_KEY` | — | Optional (Gemini vision) |

---

## Architecture

### Routing pipeline

```
L1 Router  — Ollama classifies intent (e.g. Fix.Bug, Architecture.Agent)
           — Resolves required capabilities from intent_map.json
           — Scores models in registry against those capabilities
           — Applies complexity gate (danger keywords → escalate)

L2 Executor — Runs the selected model
            — Quality gate: judge model scores output 0–1
            — Score < 0.55 → flag for review (skill mode) or retry cloud (standalone)

L3 Governor — Optional cloud validation for architecture/spec tasks (standalone only)
```

### Model roles (defaults)

| Registry key | Default model | Role |
|---|---|---|
| `ollama_qwen_coder` | `qwen3-coder:30b` | Code review, bug fix, tests |
| `ollama_deepseek` | `deepseek-r1:14b` | Security audit, deep reasoning |
| `ollama_gemma` | `gemma4:12b` | Research, docs, analysis |
| `ollama_qwen_fast` | `qwen3:8b` | Fast assistant, classification, triage |
| `ollama_llava` | `llava:latest` | Vision, UI screenshots |
| `codex_primary` | `gpt-4o` | Cloud code tasks (standalone) |
| `claude_architect` | `claude-opus-4-8` | Cloud reasoning/architecture (standalone) |

Change any model: edit `configs/model_registry.yaml` or run `preset apply auto`.

---

## RAM presets

Pick a preset that fits your Ollama server:

```bash
python3 godmode_cli.py preset list          # see all tiers
python3 godmode_cli.py preset apply auto    # auto-detect and apply
python3 godmode_cli.py preset apply 16gb    # apply a specific tier
```

| Tier | Min RAM | Best for |
|------|---------|----------|
| `6gb` | 5 GB | Entry — lightweight models only |
| `8gb` | 7 GB | Standard — 7B class models |
| `16gb` | 14 GB | Mid-range — 14B class |
| `32gb` | 28 GB | High-end — 30B class |
| `64gb` | 56 GB | Workstation — 70B+ |

---

## Quality gate

After every local model response, a judge model (`qwen3:8b`) scores the output 0–1. If the score falls below **0.55**:

- **Skill mode** — result is wrapped in a `NEEDS REVIEW` block and logged for manual review.
- **Standalone mode** — request is retried on the cloud fallback chain.

The gate fails open: if the judge is unreachable the original result is returned unchanged.

---

## Stats dashboard

```bash
python3 godmode_cli.py stats
```

Shows token usage, per-model breakdown, cost savings vs Claude Opus and GPT-4o, and a verdict:

```
  PERFECT   100% local — saved ~$1.24 vs Claude Opus. Keep it up!
  WINNING   82% local — ~$0.91 saved vs Opus. Nice efficiency.
  NEUTRAL   55% local, 45% cloud — $0.43 saved.
  WARNING   Only 20% local — most tokens are hitting the cloud.
  IN THE RED  0% local — all requests went to cloud.
```

---

## Testing

```bash
# Fast (no Ollama needed)
python3 -m pytest tests/ -m "not integration" -q

# With coverage
python3 godmode_cli.py coverage

# Live integration tests (Ollama must be running)
python3 -m pytest tests/ -m integration -v
```

121 tests · 72% line coverage (remaining gaps require live API keys or Ollama).

---

## Project layout

```
godmode/
  godmode_cli.py          # CLI entry point
  setup_wizard.py         # First-run setup
  main.py                 # orchestrate() — the core execution loop
  agents/                 # OllamaUtilityAgent, CodexEngineerAgent, ClaudeArchitectAgent, GeminiVisionAgent
  routing/                # router, capability_resolver, model_selector, quality_gate, preset_manager, model_recommender
  metrics/                # MetricsEngine — savings calculations + cheer verdict
  memory/                 # MemoryManager — task log persistence
  configs/                # model_registry.yaml, model_presets.yaml, api_config.yaml
  evaluation/             # run_routing_eval.py + routing_cases.json (11 cases)
  skills/godmode-runtime/ # Claude Code skill wrapper (SKILL.md, health_check, validate_registry)
  tests/                  # 121 tests across 6 files
  docs/                   # TEST_COVERAGE.md, system_overview.md
```

---

## License

MIT
