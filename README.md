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

[![Version](https://img.shields.io/badge/version-v0.5.1-blue)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://github.com/ronjunevaldoz/godmode/actions/workflows/ci.yml/badge.svg)](https://github.com/ronjunevaldoz/godmode/actions/workflows/ci.yml)
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
  ├─ L2 Executor run selected model (streams tokens live)
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

# 3. Configure — interactive wizard detects Ollama, assigns models, writes .env.local
python3 godmode_cli.py setup

# 4. Run
python3 godmode_cli.py run "Explain the SOLID principles with examples"
python3 godmode_cli.py stats
```

**Remote Ollama server?** Set the base URL — no path suffix needed:
```bash
# In .env.local (created by setup wizard)
OLLAMA_BASE_URL=https://your-server/ollama   # ✓ base URL only
OLLAMA_BASE_URL=http://192.168.1.100:11434   # ✓ IP address
# NOT: https://your-server/ollama/api/chat   # ✗ don't include /api/chat
```

---

## Use as an MCP server

Expose godmode as a native Claude tool — no CLI shelling needed. Claude can call `run`, `run_session`, `stats`, and `models` directly from any conversation.

**Requires:** `GODMODE_PATH` set in your shell profile (see below).

The project includes a `.mcp.json` that auto-resolves the server path via `GODMODE_PATH`. Claude Code picks it up automatically when you open the project.

To register it globally (available in all projects):

```bash
# Add to ~/.claude/settings.json under "mcpServers"
{
  "mcpServers": {
    "godmode": {
      "command": "sh",
      "args": ["-c", "exec python3 \"$(dirname \"$GODMODE_PATH\")/mcp_server.py\""]
    }
  }
}
```

**Available MCP tools:**

| Tool | What it does |
|------|-------------|
| `run` | Route and execute a prompt |
| `run_session` | Route with persistent session history |
| `stats` | Savings dashboard |
| `models` | List Ollama model registry |

---

## Installation

Full installation guide for all environments (Claude Code, Claude Desktop, Cursor, Continue, Windsurf, Codex CLI, Gemini CLI): [docs/INSTALL.md](docs/INSTALL.md)

## Install as a Claude Code skill

```bash
npx skills add ronjunevaldoz/godmode   # install
npx skills update godmode-runtime      # update to latest
```

**Add to your shell profile** so the skill can find the CLI from any session:
```bash
# Add to ~/.zshrc or ~/.bashrc
export GODMODE_PATH="$(find ~ -maxdepth 5 -name 'godmode_cli.py' -not -path '*/__pycache__/*' 2>/dev/null | head -1)"
```
Then `source ~/.zshrc` and the skill auto-resolves the path every time.

**Allow the CLI in Claude Code settings** (Settings → Permissions → Add Rule):
```
Bash(python3 /your/path/to/godmode_cli.py *)
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
| `run "prompt"` | Route and execute a prompt (streams tokens live) |
| `run "prompt" --session <name>` | Multi-turn conversation with persistent history |
| `session list` | List saved sessions |
| `session show <name>` | Print conversation history |
| `session clear <name>` | Delete a session |
| `stats` | Token savings dashboard + verdict |
| `report` | Failure log — flagged runs grouped by intent, avg quality scores |
| `models` | List pulled Ollama models, research registry targets, or pull missing ones |
| `preset list` | RAM-tiered preset matrix |
| `preset apply auto` | Auto-detect server RAM, apply best preset |
| `recommend` | Score pulled models, suggest registry changes |
| `recommend --apply` | Apply recommendations to registry |
| `recommend --pull` | Show registry-driven model research and pull missing Ollama models |
| `benchmark` | Compare local models on a small prompt suite |
| `models research` | Show registry-driven model recommendations and missing pulls |
| `models pull` | Pull enabled Ollama registry models that are missing locally |
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
| `ollama_qwythos` | `hf.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF:Q4_K_M` | Long-context research, reasoning |
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

**Key env vars** (set in `.env.local`):

```bash
OLLAMA_BASE_URL=http://localhost:11434   # base URL only — no /api/chat suffix
OLLAMA_SERVER_RAM_GB=32                 # improves preset auto-selection
GODMODE_MODE=skill                      # skill | standalone
ANTHROPIC_API_KEY=...                   # standalone only
OPENAI_API_KEY=...                      # standalone only
```

**Shell env vars** (set in `~/.zshrc` or `~/.bashrc`):

```bash
# Required for the Claude Code skill to find the CLI
export GODMODE_PATH="$(find ~ -maxdepth 5 -name 'godmode_cli.py' -not -path '*/__pycache__/*' 2>/dev/null | head -1)"
```

---

## Quality gate

Every local response is scored 0–1 by a judge model (`qwen3:8b`). Score < **0.55**:

- **Skill mode** → result wrapped in `⚠ NEEDS REVIEW` block, flagged in memory
- **Standalone mode** → retried on cloud fallback chain

Fails open — if the judge is unreachable, the original result passes through.

---

## Multi-turn sessions

```bash
python3 godmode_cli.py run "What is the repository pattern?" --session myproject
python3 godmode_cli.py run "Show me a Python example"        --session myproject
python3 godmode_cli.py run "Now add error handling"          --session myproject

python3 godmode_cli.py session list              # list all sessions
python3 godmode_cli.py session show myproject    # view history
python3 godmode_cli.py session clear myproject   # wipe it
```

History is budget-trimmed to ~2k tokens per request to avoid overflowing smaller models.

---

## Testing

```bash
python3 -m pytest tests/ -m "not integration" -q   # fast, no Ollama needed
python3 godmode_cli.py coverage                     # with coverage report
python3 -m pytest tests/ -m integration -v         # live Ollama required
```

130 tests · 72% line coverage

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
├── memory/                 MemoryManager · SessionManager — task log + conversation history
├── configs/                model_registry.yaml · model_presets.yaml
├── evaluation/             11 routing accuracy test cases
├── skills/godmode-runtime/ Claude Code skill wrapper
└── tests/                  130 tests across 7 files
```

---

## License

MIT — [ronjunevaldoz/godmode](https://github.com/ronjunevaldoz/godmode)
