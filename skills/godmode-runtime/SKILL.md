---
name: godmode-runtime
description: Local-first AI routing runtime. Routes prompts to the best model (Ollama local or cloud) based on intent, capability, and cost. Tracks savings vs Claude Opus. Works inside Claude Desktop with no API keys needed.
---

# Godmode Runtime

## How to invoke

Before running any godmode command, resolve the CLI path dynamically:

```bash
# 1. Prefer GODMODE_PATH env var (set in shell profile for permanent fix)
# 2. Fall back to searching the home directory for godmode_cli.py
GODMODE_CLI="${GODMODE_PATH:-$(find ~ -maxdepth 5 -name 'godmode_cli.py' -not -path '*/__pycache__/*' 2>/dev/null | head -1)}"

if [ -z "$GODMODE_CLI" ]; then
  echo "godmode not found. Add to your shell profile: export GODMODE_PATH=/path/to/godmode_cli.py"
  exit 1
fi
```

**Permanent fix** — add to `~/.zshrc` or `~/.bashrc` so every session picks it up automatically:
```bash
export GODMODE_PATH="$(find ~ -maxdepth 5 -name 'godmode_cli.py' -not -path '*/__pycache__/*' 2>/dev/null | head -1)"
```

Then run commands using `$GODMODE_CLI`:

```bash
python3 "$GODMODE_CLI" run "the user's prompt"
python3 "$GODMODE_CLI" run "prompt" --session <name>   # multi-turn
python3 "$GODMODE_CLI" stats                           # savings dashboard
python3 "$GODMODE_CLI" models                          # list available models
python3 "$GODMODE_CLI" session list                    # list sessions
```

> **Permission note:** Add a Bash allow rule in Claude Code settings for the resolved path, e.g.:
> `Bash(python3 /your/path/to/godmode_cli.py *)`
>
> Or set `GODMODE_PATH=/path/to/godmode_cli.py` in your shell profile so the skill finds it automatically.

Godmode is a local-first AI routing runtime. It classifies the intent of any prompt, matches required capabilities to a model registry, and executes — preferring free local Ollama models over paid cloud APIs. After every session it shows how much you saved.

## Setup (first time)

```bash
git clone https://github.com/ronjunevaldoz/godmode.git
cd godmode
pip install -r requirements.txt
python3 godmode_cli.py setup   # interactive wizard — detects Ollama, assigns models
```

The wizard will:
1. Ask for your Ollama URL (default: `http://localhost:11434`)
2. List all pulled models and let you assign each to a role
3. Pick operating mode (`skill` for Claude Desktop, `standalone` for independent use)
4. Write `.env.local` and patch `configs/model_registry.yaml`

## Running prompts

```bash
python3 godmode_cli.py run "Fix the null pointer in the payment handler"
python3 godmode_cli.py run "Summarise this log file and find anomalies"
python3 godmode_cli.py run "Design a microservices auth architecture"
```

Each run prints the routed model, mode tag (`[SKILL]` / `[STANDALONE]`), and the result. High-stakes tasks (bug fixes, security reviews) are wrapped in a `NEEDS REVIEW` block in skill mode.

## All commands

```bash
python3 godmode_cli.py setup              # First-run wizard
python3 godmode_cli.py run "prompt"       # Route and execute
python3 godmode_cli.py stats              # Savings dashboard + verdict
python3 godmode_cli.py models             # List Ollama models and assigned roles
python3 godmode_cli.py preset list        # RAM-tiered preset matrix
python3 godmode_cli.py preset apply auto  # Auto-select preset from server RAM
python3 godmode_cli.py recommend          # Score pulled models, suggest registry changes
python3 godmode_cli.py recommend --apply  # Apply recommendations
python3 godmode_cli.py eval               # Routing accuracy evaluation (11 cases)
python3 godmode_cli.py clear              # Reset task memory
python3 godmode_cli.py coverage           # Test suite with coverage report
```

## Operating modes

| Mode | How to set | Behaviour |
|------|-----------|-----------|
| `skill` *(default)* | `GODMODE_MODE=skill` | Runs inside Claude Desktop. No cloud API keys needed. High-stakes results flagged `NEEDS REVIEW`. |
| `standalone` | `GODMODE_MODE=standalone` | Runs independently. Low-quality/high-stakes results escalate to cloud automatically. |

## Routing pipeline

```
Your prompt
  → L1 Router   classify intent (via Ollama triage model)
               resolve capabilities from intent_map.json
               score + select model from model_registry.yaml
               apply complexity gate (danger keywords → escalate)
  → L2 Executor run selected model
               quality gate: judge scores output 0–1
               < 0.55 → flag (skill) or retry cloud (standalone)
  → L3 Governor optional cloud validation for arch/spec tasks
```

## Intent categories

| Intent prefix | Routes to | Example |
|---|---|---|
| `Utility.*` | local fast model | summarise, classify, extract |
| `Improve.Code` / `Review.Code` | local code model | refactor, review PR |
| `Fix.Bug` / `Review.Security` | cloud or flagged | security audit, crash fix |
| `Architecture.*` | cloud or flagged | system design, ADR |
| `Multimodal.*` | vision model | UI screenshot analysis |

## Stats & savings

```bash
python3 godmode_cli.py stats
```

Shows token usage, per-model breakdown, estimated savings vs Claude Opus and GPT-4o, and a verdict:

```
  PERFECT   100% local — saved ~$1.24 vs Claude Opus. Keep it up!
  WINNING   82% local — ~$0.91 saved. Nice efficiency.
  NEUTRAL   55% local, 45% cloud — $0.43 saved.
  WARNING   Only 20% local — run 'preset apply auto' to improve.
  IN THE RED  0% local — check Ollama is running.
```

## Model presets by RAM

```bash
python3 godmode_cli.py preset apply auto   # auto-detect server RAM and apply best tier
```

| Tier | Min RAM | Models |
|------|---------|--------|
| `6gb` | 5 GB | 1B–3B class |
| `8gb` | 7 GB | 7B class |
| `16gb` | 14 GB | 14B class |
| `32gb` | 28 GB | 30B class |
| `64gb` | 56 GB | 70B+ |

## Key config files

| File | Purpose |
|------|---------|
| `.env.local` | Your personal env vars — Ollama URL, API keys (gitignored) |
| `configs/model_registry.yaml` | Model metadata, capabilities, cost rates |
| `routing/intent_map.json` | Intent → capability mappings |

## Environment variables

| Variable | Default | Notes |
|----------|---------|-------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Point to remote server if Ollama isn't local |
| `OLLAMA_SERVER_RAM_GB` | auto-detected | Set for accurate preset recommendations |
| `GODMODE_MODE` | `skill` | `skill` or `standalone` |
| `ANTHROPIC_API_KEY` | — | Only needed in `standalone` mode |
| `OPENAI_API_KEY` | — | Only needed in `standalone` mode |
| `GOOGLE_API_KEY` | — | Optional — Gemini vision model |

## Source

https://github.com/ronjunevaldoz/godmode
