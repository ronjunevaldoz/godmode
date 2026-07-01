# Changelog

All notable changes to godmode are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.5.1] — 2026-07-01

### Fixed
- Runtime config loads now resolve from the repository root, so `run`, `eval`, `benchmark`, and `preset` work when launched from outside the project directory
- `godmode_cli.py clear` now resets the task log using the repo-root path at runtime while preserving the existing test mock behavior

---

## [0.5.0] — 2026-06-18

### Added
- `--file` flag on `run` command — explicit file context injection; supports multiple `--file` flags
- `GODMODE_CONTEXT.md` — user-defined project context (stack, conventions, do-not-suggest rules) injected automatically for code intents
- `logs/failures.jsonl` — auto-logs every flagged run (intent, model, score, reason, truncated prompt/response)
- `godmode_cli.py report` — failure log grouped by intent, avg quality score, top failure reason
- `mcp_server.py` — MCP server exposing `run`, `run_session`, `stats`, `models` tools
- `.mcp.json` — project-level MCP registration for Claude Desktop / Cursor / Continue
- GitHub Actions CI — matrix test on Python 3.10 / 3.11 / 3.12
- Per-project `GODMODE_CONTEXT.md` — checks CWD first, falls back to godmode install dir
- `docs/INSTALL.md` — installation guide for all agent environments
- `docs/ROADMAP.md` — three-phase plan toward community platform
- `docs/RELEASE.md` — release process guide

### Changed
- `_build_file_context()` replaces regex-only `_inject_file_context()` — explicit paths always win, regex is fallback
- `orchestrate()` accepts `files: list[str] | None`
- Quality gate now scores against `user_input` not `execution_prompt` (was scoring file content, not the task)
- `GODMODE_CONTEXT.md` checks `Path.cwd()` first (per-project), then godmode dir (global)
- `session_manager.truncate_to_budget()` — oversized single message now truncated, not silently passed whole
- Quality gate: malformed judge JSON returns `0.5` (uncertain) not `1.0` (false pass)
- History validation in `_build_messages()` — drops malformed entries, logs count
- `fallback_chain.yaml` load wrapped in try/except — missing file no longer crashes at import

### Fixed
- Hallucinations on code tasks caused by missing file context
- Quality gate false-pass when judge model returns non-JSON
- Session budget silently exceeded by single oversized message
- Dead code: redundant `Path.cwd()` fallback in file injection

---

## [0.4.0] — 2026-06-15

### Added
- Streaming responses — `OllamaUtilityAgent._execute_streaming()` with live token output
- Multi-turn sessions — `SessionManager` persists history as JSON, budget-trimmed to 8000 chars
- `--session <name>` flag on `run` command
- `godmode_cli.py session` subcommands: `list`, `show`, `clear`
- Setup wizard (`setup_wizard.py`) — interactive first-run: Ollama URL, model roles, mode, writes `.env.local`
- `godmode_cli.py setup` command
- `python-dotenv` support — loads `.env.local` then `.env` at startup

### Changed
- `OLLAMA_BASE_URL` normalized to base URL only in all modules — `/api/chat` appended at call site
- Removed hardcoded personal Ollama URL from all source files

---

## [0.3.0] — 2026-06-10

### Added
- Quality gate — `qwen3:8b` judge scores local output 0–1; score < 0.55 triggers flag or cloud retry
- 4-tier escalation: governance / high-stakes / danger keywords / low-confidence
- Preset manager — RAM-tiered model presets (`6gb` → `64gb`)
- Model recommender — scores pulled models, suggests registry changes
- `godmode_cli.py recommend`, `preset` commands
- Remote Ollama support via `OLLAMA_BASE_URL`

---

## [0.2.0] — 2026-06-05

### Added
- Metrics engine — tracks token savings vs Claude Opus and GPT-4o
- `godmode_cli.py stats` — savings dashboard with WINNING/PERFECT/WARNING verdict
- Skills.sh publishing — `npx skills add ronjunevaldoz/godmode`
- Health check hook on session start

---

## [0.1.0] — 2026-06-01

### Added
- Core routing loop: intent → capability → model registry → execution
- Local Ollama agents: qwen3:8b (fast), qwen3-coder:30b (code), deepseek-r1:14b (reasoning)
- Cloud agents: Claude (Anthropic), Codex (OpenAI), Gemini (Google)
- `configs/model_registry.yaml` and `routing/intent_map.json`
- `godmode_cli.py` with `run`, `eval`, `stats`, `clear`, `models` commands
- MIT license
