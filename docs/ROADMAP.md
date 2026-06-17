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

- Simple Next.js or static site
- Reads from a JSON endpoint (can start with a GitHub Gist)
- Charts: savings over time, intent distribution, quality score trends, top failure reasons
- No backend required — personal data only

---

## Phase 3 — Community platform

**Goal:** aggregate anonymized reports across users to crowdsource routing improvements.

- Users opt-in via `godmode_cli.py submit`
- Public dashboard: which `intent × model` pairs fail most across all users
- Submitted reports feed back into `intent_map.json` and `model_registry.yaml` improvements
- Leaderboard: best local model per intent category based on community quality scores

---

## Deferred / out of scope for now

- Docker image
- Web UI for the CLI (terminal output is sufficient)
- Watch mode / stdin streaming
