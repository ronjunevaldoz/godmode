# Godmode Roadmap

## Status: Core complete

The core routing loop is production-ready:
- Intent → capability → model registry → execution
- Streaming responses + multi-turn sessions
- Quality gate (score < 0.55 → flag or cloud retry)
- File context injection (auto-reads files mentioned in prompt)
- Per-project `GODMODE_CONTEXT.md` (user-defined stack/conventions)
- Failure logging → `logs/failures.jsonl`
- GitHub Actions CI + MCP server

---

## Phase 1 — Data pipeline

**Goal:** clean, anonymized submission format before any external service is built.

- Anonymize `logs/failures.jsonl` before submission: strip file contents, keep only `intent + model + score + reason + ts`
- `godmode_cli.py submit` — opt-in command, sends anonymized stats to a configured endpoint
- Define and freeze the submission JSON schema

**Why first:** the website has nothing to display without a stable data format.

---

## Phase 2 — Personal dashboard (website)

**Goal:** visualize your own godmode stats in a browser.

**Stack:** Next.js · shadcn/ui · Vercel (deploy) · Vercel agent skills (AI-assisted build)

- Charts: savings over time, intent distribution, quality score trends, top failure reasons
- Reads from Phase 1 submission endpoint (or local JSON export as fallback)
- Use `npx skills add vercel-labs/agent-skills` to accelerate UI scaffolding
- Deploy to Vercel — zero config, free tier sufficient for personal dashboard

### Design guidance

Layout: top nav (Dashboard · Reports · Models · Settings) + user avatar. Four metric cards across the top (total runs, saved vs Opus, local rate, avg quality). Two-column chart row below (intent distribution donut + 30-day quality score trend line). Bottom row: recent failures table + model usage bar chart with efficiency verdict.

**Quality score color coding:**
- `score ≥ 0.70` → green badge
- `0.50 ≤ score < 0.70` → amber badge
- `score < 0.50` → red badge

**Submit report flow (Phase 3 entry point):**
"Submit report" button in the failures table triggers a confirmation panel showing the anonymized payload (intent, model, score, reason, ts — no prompt text, no file contents). User confirms → sent via `godmode_cli.py submit` or MCP `godmode.submit()`. Prompt suggestion pattern: button calls `sendPrompt('godmode submit --preview')` so the user sees what will be sent before it goes out.

---

## Phase 3 — Community platform

**Goal:** aggregate anonymized reports across users to crowdsource routing improvements.

**Submission:** via existing godmode MCP tool or CLI — no new client tooling needed.
- MCP: `godmode.submit()` tool callable from Claude Desktop
- CLI: `godmode_cli.py submit` opt-in command
- Both send the same anonymized schema defined in Phase 1

**Platform:**
- Public dashboard (same stack as Phase 2) showing cross-user failure patterns
- Which `intent × model` pairs fail most across all installs
- Leaderboard: best local model per intent based on community quality scores
- Submitted reports feed back into `intent_map.json` and `model_registry.yaml` improvements

---

## Deferred / out of scope for now

- Docker image
- Web UI for the CLI (terminal output is sufficient)
- Watch mode / stdin streaming
