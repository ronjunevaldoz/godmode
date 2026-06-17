<div align="center">

```
  ██████╗  ██████╗ ██████╗ ███╗   ███╗ ██████╗ ██████╗ ███████╗
 ██╔════╝ ██╔═══██╗██╔══██╗████╗ ████║██╔═══██╗██╔══██╗██╔════╝
 ██║  ███╗██║   ██║██║  ██║██╔████╔██║██║   ██║██║  ██║█████╗
 ██║   ██║██║   ██║██║  ██║██║╚██╔╝██║██║   ██║██║  ██║██╔══╝
 ╚██████╔╝╚██████╔╝██████╔╝██║ ╚═╝ ██║╚██████╔╝██████╔╝███████╗
  ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝
```

**Local-first AI routing runtime.**  
Route any prompt to the right model. Keep it free. Track every dollar saved.

[![Python](https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-121%20passing-brightgreen?logo=pytest&logoColor=white)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-72%25-yellow)](docs/TEST_COVERAGE.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Skill](https://img.shields.io/badge/skills.sh-godmode--runtime-8b5cf6?logo=anthropic&logoColor=white)](https://skills.sh/ronjunevaldoz/godmode/godmode-runtime)
[![Local First](https://img.shields.io/badge/local--first-Ollama-f97316?logo=ollama&logoColor=white)](https://ollama.com)

</div>

---

## What it does

Godmode sits between you and your models. Every prompt is classified, routed to the most capable (and cheapest) model available, and executed. Local Ollama models handle most of the work for free — cloud APIs only kick in for high-stakes tasks that need them.

```
Your prompt
  │
  ├─ L1 Router   classify intent → resolve capabilities → score + select model
  │              complexity gate: danger keywords escalate before execution
  │
  ├─ L2 Executor run selected model
  │              quality gate: judge scores output 0–1  (< 0.55 = flag or retry)
  │
  └─ L3 Governor optional cloud validation for arch / spec tasks
```

---

## Quickstart

```bash
# 1. Clone and install
git clone https://github.com/ronjunevaldoz/godmode.git && cd godmode
pip install -r requirements.txt

# 2. Pull at least one Ollama model
ollama pull qwen3:8b

# 3. Configure (interactive — detects models, writes .env.local)
python3 godmode_cli.py setup

# 4. Run
python3 godmode_cli.py run "Explain the SOLID principles with examples"
python3 godmode_cli.py stats
```

Or install as a Claude Code skill:

```bash
npx skills add ronjunevaldoz/godmode
```

---

## Operating modes

| Mode | When to use | Cloud keys needed |
|------|-------------|-------------------|
| `skill` *(default)* | Running inside Claude Desktop | No — Claude is the reviewer |
| `standalone` | Running independently | Yes — for auto cloud escalation |

Set via `GODMODE_MODE=skill` or `GODMODE_MODE=standalone` in `.env.local`.

---

## Commands

| Command | What it does |
|---------|-------------|
| `setup` | First-run wizard — Ollama URL, model roles, mode |
| `run "prompt"` | Route and execute a prompt |
| `stats` | Token savings dashboard + verdict |
| `models` | List pulled Ollama models and assigned roles |
| `preset list` | RAM-tiered preset matrix |
| `preset apply auto` | Auto-detect server RAM, apply best preset |
| `recommend` | Score pulled models, suggest registry changes |
| `recommend --apply` | Apply recommendations to registry |
| `eval` | Routing accuracy evaluation (11 cases) |
| `clear` | Reset task memory |
| `coverage` | Test suite with line coverage |

---

## Savings dashboard

```
╔══════════════════════════════════════════════════════════╗
║            Godmode Token Savings Dashboard               ║
╚══════════════════════════════════════════════════════════╝

  Total Requests :  42

  LOCAL  (free)    38 requests  90.5%
    ├─ qwen3:8b                 21 runs   fast assistant · classification
    ├─ qwen3-coder:30b          12 runs   code review · bug fix · unit tests
    └─ deepseek-r1:14b           5 runs   audit · security · prompt quality
  Tokens processed : ~184,200   Cost: $0.00

  CLOUD  (paid)     4 requests   9.5%
  Tokens processed : ~8,400   Cost: $0.0063

  ──────────────────────────────────────────────────────────
  ESTIMATED SAVINGS (local tasks vs cloud alternatives)
  vs Claude Opus  : $2.7630
  vs GPT-4o       : $0.4605

  ──────────────────────────────────────────────────────────

  WINNING  90% local — ~$2.76 saved vs Opus. Nice efficiency.
```

Verdicts: `PERFECT` · `WINNING` · `NEUTRAL` · `WARNING` · `IN THE RED`

---

## Model roles

| Role | Default model | Used for |
|------|--------------|---------|
| `ollama_qwen_coder` | `qwen3-coder:30b` | Code review, bug fix, tests |
| `ollama_deepseek` | `deepseek-r1:14b` | Security audit, deep reasoning |
| `ollama_gemma` | `gemma4:12b` | Research, docs, analysis |
| `ollama_qwen_fast` | `qwen3:8b` | Fast tasks, classification, triage |
| `ollama_llava` | `llava:latest` | Vision, UI screenshots |
| `codex_primary` | `gpt-4o` | Cloud code (standalone only) |
| `claude_architect` | `claude-opus-4-8` | Cloud reasoning (standalone only) |

Swap any model: `python3 godmode_cli.py preset apply auto` picks the best set for your server's RAM.

---

## RAM presets

| Tier | Min RAM | Model class |
|------|---------|-------------|
| `6gb` | 5 GB | 1B–3B |
| `8gb` | 7 GB | 7B |
| `16gb` | 14 GB | 14B |
| `32gb` | 28 GB | 30B |
| `64gb` | 56 GB | 70B+ |

```bash
python3 godmode_cli.py preset apply auto   # auto-selects based on server RAM
python3 godmode_cli.py preset apply 32gb   # or pick a tier directly
```

---

## Configuration

| File | Purpose |
|------|---------|
| `.env.local` | Personal env vars — gitignored, created by `setup` |
| `.env.example` | Template to copy |
| `configs/model_registry.yaml` | Model metadata, capabilities, cost rates |
| `routing/intent_map.json` | Intent → capability mappings |

**Key env vars:**

```bash
OLLAMA_BASE_URL=http://localhost:11434   # remote server: https://your-host/ollama
OLLAMA_SERVER_RAM_GB=32                 # improves preset auto-selection
GODMODE_MODE=skill                      # skill | standalone
ANTHROPIC_API_KEY=...                   # standalone only
OPENAI_API_KEY=...                      # standalone only
```

---

## Quality gate

Every local response is scored 0–1 by a judge model (`qwen3:8b`). Score < **0.55**:

- **Skill mode** → result wrapped in `⚠ NEEDS REVIEW` block, flagged in memory
- **Standalone mode** → retried on cloud fallback chain

Fails open — if the judge is unreachable, the original result passes through.

---

## Testing

```bash
python3 -m pytest tests/ -m "not integration" -q   # fast, no Ollama needed
python3 godmode_cli.py coverage                     # with coverage report
python3 -m pytest tests/ -m integration -v         # live Ollama required
```

121 tests · 72% line coverage

---

## Project layout

```
godmode/
├── godmode_cli.py          CLI entry point + all commands
├── setup_wizard.py         Interactive first-run setup
├── main.py                 orchestrate() — core execution loop
├── agents/                 OllamaUtilityAgent · CodexEngineer · ClaudeArchitect · GeminiVision
├── routing/                router · capability_resolver · model_selector
│                           quality_gate · preset_manager · model_recommender
├── metrics/                MetricsEngine — savings + cheer verdict
├── memory/                 MemoryManager — task log persistence
├── configs/                model_registry.yaml · model_presets.yaml
├── evaluation/             11 routing accuracy test cases
├── skills/godmode-runtime/ Claude Code skill wrapper
└── tests/                  121 tests across 6 files
```

---

## License

MIT — [ronjunevaldoz/godmode](https://github.com/ronjunevaldoz/godmode)
