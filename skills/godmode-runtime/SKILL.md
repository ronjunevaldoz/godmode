---
name: godmode-runtime
description: >
  Godmode is a local-first AI routing runtime that sends prompts to the
  cheapest capable model — Ollama locally first, cloud only when needed.
  Use this skill whenever the user wants to: run a prompt through godmode,
  do a code review with --file to avoid hallucinations, start or resume a
  --session, check token savings vs Claude Opus, configure the Ollama URL
  or model registry, understand or fix a NEEDS REVIEW result, tune routing
  thresholds, run the eval suite, or manage sessions. Also invoke when the
  user mentions godmode_cli, local AI routing, or cost-saving model routing.
---

# Godmode Runtime

## What it does

Godmode routes every prompt through a 3-layer pipeline:

1. **L1 Router** — classifies intent, resolves required capabilities, picks the cheapest model that can handle it (Ollama local first)
2. **L2 Executor** — runs the model, streams output live, then scores quality 0–1 with a local judge
3. **L3 Governor** — if score < 0.55, flags `⚠ NEEDS REVIEW` (skill mode) or retries with a cloud model (standalone mode)

**Result:** You get fast, cheap answers for simple tasks. Hard tasks escalate automatically. Every run is tracked so you can see exactly how much you saved vs Claude Opus.

---

## Example use cases

### 1. Code review without hallucinations
You have a Kotlin service. You want a security review but the local model keeps suggesting Spring patterns that don't exist in your codebase.

```bash
# Always pass the file — model can't access your filesystem otherwise
python3 "$GODMODE_CLI" run "check for authorization bypass and missing input validation" \
  --file src/services/SalaryServiceImpl.kt
```

With `GODMODE_CONTEXT.md` in your project root declaring your stack (Kotlin + Ktor + MongoDB, no Spring), godmode injects it automatically. The model now reviews your actual code instead of inventing Java patterns.

---

### 2. Multi-turn code audit session
You want to audit a service across multiple prompts without losing context.

```bash
python3 "$GODMODE_CLI" run "security review" --file src/PaymentService.kt --session payment-audit
python3 "$GODMODE_CLI" run "now write the fixes for the issues you found" --file src/PaymentService.kt --session payment-audit
python3 "$GODMODE_CLI" run "add unit tests for the fixed methods" --file src/PaymentService.kt --session payment-audit
```

Each turn remembers the previous exchange. The session is budget-trimmed to 8000 chars automatically.

---

### 3. Cross-file comparison
You refactored a service and want to check for regressions between the old and new version.

```bash
python3 "$GODMODE_CLI" run "find any logic that was in the old version but is missing or changed in the new one" \
  --file src/old/GuildService.kt \
  --file src/new/GuildService.kt
```

---

### 4. Track how much you've saved
See how much cheaper godmode is vs always using Claude Opus or GPT-4o.

```bash
python3 "$GODMODE_CLI" stats
```

Output: total runs, tokens routed locally vs cloud, estimated savings in dollars, verdict (WINNING / PERFECT / WARNING).

---

### 5. Understand and fix a NEEDS REVIEW result
The output came back wrapped in `⚠ NEEDS REVIEW`. The quality judge scored it below 0.55 — the model gave a low-confidence answer.

```bash
# Option 1: check what went wrong
python3 "$GODMODE_CLI" report

# Option 2: retry with cloud escalation
GODMODE_MODE=standalone ANTHROPIC_API_KEY=... python3 "$GODMODE_CLI" run "your prompt" --file src/Foo.kt
```

`report` groups failures by intent and shows the average quality score and top failure reason per category.

---

### 6. Configure which model handles which task
You just pulled a new model and want to assign it to code review tasks.

```bash
python3 "$GODMODE_CLI" models          # see what's pulled and what role each has
python3 "$GODMODE_CLI" models research # registry-driven recommendations + missing pulls
python3 "$GODMODE_CLI" models pull     # pull any enabled Ollama registry models that are missing
python3 "$GODMODE_CLI" models pull ollama_qwythos  # pull and enable a specific experimental model
python3 "$GODMODE_CLI" recommend       # get suggestions based on your pulled models
python3 "$GODMODE_CLI" recommend --apply   # apply them to model_registry.yaml
```

Or edit `configs/model_registry.yaml` directly — the `routing/intent_map.json` maps intent categories to capability requirements.

---

### 7. Point godmode at a remote Ollama server
Your Ollama is running on a different machine (e.g. a home server with a big GPU).

```bash
OLLAMA_BASE_URL=http://192.168.1.10:11434 python3 "$GODMODE_CLI" run "your prompt"
```

Or set it permanently in `.env.local` (created by `setup`):
```
OLLAMA_BASE_URL=http://192.168.1.10:11434
```

---

### 8. General reasoning (no file needed)
Not every task needs a file. Pure reasoning, architecture questions, and writing tasks route to the best available model automatically.

```bash
python3 "$GODMODE_CLI" run "design a rate-limiting strategy for a multi-tenant API with per-guild quotas"
python3 "$GODMODE_CLI" run "explain the tradeoffs between CQRS and a simple service layer for this use case"
```

---

## Reducing hallucinations — read this first

Local models hallucinate when they have no real context to work from. There are four failure modes and how to prevent each:

**1. No file content → model invents generic code**

The model cannot access the filesystem. Without `--file` it receives only the prompt text and will generate advice for a completely different language/framework.

Always pass the actual file:
```bash
# Wrong — model has no code, will hallucinate Spring/Java for a Kotlin/Ktor service
python3 "$GODMODE_CLI" run "security review on SalaryServiceImpl"

# Correct — model receives the real code
python3 "$GODMODE_CLI" run "security review" --file src/services/SalaryServiceImpl.kt
```

**2. No project context → model guesses the wrong stack**

Create `GODMODE_CONTEXT.md` in the project root once. Godmode injects it automatically for code tasks.

```markdown
## Stack
- Language: Kotlin · Framework: Ktor · Database: MongoDB
- Auth: JWT, per-guild scoping via guildId
- No Spring — never suggest @PreAuthorize, JDBC, or calculateBonus
```

Without this, the model defaults to the most common patterns it was trained on (Spring/Java, SQL, etc.) even when reviewing Kotlin/Mongo code.

**3. Vague prompt → model fills in blanks with assumptions**

Specific prompts produce grounded output. Vague prompts invite invention.

```bash
# Vague — model decides what to look for
python3 "$GODMODE_CLI" run "review this" --file src/PaymentService.kt

# Specific — model focuses on real concerns
python3 "$GODMODE_CLI" run "check for double-payment vulnerabilities and missing input validation" \
  --file src/PaymentService.kt
```

**4. Ignoring NEEDS REVIEW → acting on bad output**

When godmode wraps a result in `⚠ NEEDS REVIEW`, the quality gate scored it below 0.55. Treat that output as a draft, not a recommendation. Either verify it manually or re-run in standalone mode with an API key for cloud retry.

---

## Before invoking godmode for any code task

Run through this checklist:

- [ ] Do I have the file path? (not just the class name — the actual `.kt`/`.py`/`.ts` path)
- [ ] Is `GODMODE_CONTEXT.md` in the project root with the stack/conventions?
- [ ] Is my prompt specific enough to constrain the output?

If any box is unchecked, fix it before invoking. The quality of godmode output is directly proportional to the context you give it.

---

## Command reference

```bash
# Code tasks — --file is required
python3 "$GODMODE_CLI" run "security review"           --file src/services/SalaryServiceImpl.kt
python3 "$GODMODE_CLI" run "find and fix the bug"      --file app/routes/auth.py
python3 "$GODMODE_CLI" run "write unit tests"          --file utils/parser.ts
python3 "$GODMODE_CLI" run "refactor for readability"  --file core/engine.go

# Multiple files (compare, cross-file bugs, shared interfaces)
python3 "$GODMODE_CLI" run "find inconsistencies between these" \
  --file src/old/PaymentService.kt \
  --file src/new/PaymentService.kt

# Multi-turn session on the same file
python3 "$GODMODE_CLI" run "security review"        --file src/SalaryServiceImpl.kt --session audit
python3 "$GODMODE_CLI" run "now write the fixes"    --file src/SalaryServiceImpl.kt --session audit

# General tasks (no file needed)
python3 "$GODMODE_CLI" run "design a microservices auth architecture"
python3 "$GODMODE_CLI" run "explain the repository pattern with examples"
```

---

## How to invoke

Resolve the CLI path before running any command:

```bash
GODMODE_CLI="${GODMODE_PATH:-$(find ~ -maxdepth 5 -name 'godmode_cli.py' -not -path '*/__pycache__/*' 2>/dev/null | head -1)}"

if [ -z "$GODMODE_CLI" ]; then
  echo "godmode not found. Add to your shell profile: export GODMODE_PATH=/path/to/godmode_cli.py"
  exit 1
fi
```

**Permanent fix** — add to `~/.zshrc` or `~/.bashrc`:
```bash
export GODMODE_PATH="$(find ~ -maxdepth 5 -name 'godmode_cli.py' -not -path '*/__pycache__/*' 2>/dev/null | head -1)"
```

> **Permission note:** Add a Bash allow rule in Claude Code settings:
> `Bash(python3 /your/path/to/godmode_cli.py *)`

---

## Setup (first time)

```bash
git clone https://github.com/ronjunevaldoz/godmode.git
cd godmode
pip install -r requirements.txt
python3 godmode_cli.py setup   # interactive wizard — detects Ollama, assigns models
```

Then create `GODMODE_CONTEXT.md` in your project root (see section above).

---

## All commands

```bash
python3 godmode_cli.py setup                              # First-run wizard
python3 godmode_cli.py run "prompt"                       # Route and execute
python3 godmode_cli.py run "prompt" --file src/Foo.kt     # With file context
python3 godmode_cli.py run "prompt" --file a.kt --file b.kt  # Multiple files
python3 godmode_cli.py run "prompt" --session <name>      # Multi-turn session
python3 godmode_cli.py stats                              # Savings dashboard + verdict
python3 godmode_cli.py report                             # Failure log by intent
python3 godmode_cli.py models                             # List Ollama models and roles
python3 godmode_cli.py models research                    # Registry-driven recommendations + missing pulls
python3 godmode_cli.py models pull                        # Pull enabled Ollama registry models
python3 godmode_cli.py models pull ollama_qwythos         # Pull and enable Qwythos explicitly
python3 godmode_cli.py preset apply auto                  # Auto-select preset from RAM
python3 godmode_cli.py recommend                          # Suggest registry improvements
python3 godmode_cli.py recommend --apply                  # Apply recommendations
python3 godmode_cli.py recommend --pull                   # Show registry-driven model research + pull missing models
python3 godmode_cli.py benchmark                          # Compare local models on a small prompt suite
python3 godmode_cli.py session list                       # List saved sessions
python3 godmode_cli.py session show <name>                # Print session history
python3 godmode_cli.py session clear <name>               # Delete a session
python3 godmode_cli.py eval                               # Routing accuracy evaluation
python3 godmode_cli.py clear                              # Reset task memory
```

---

## Operating modes

| Mode | How to set | Behaviour |
|------|-----------|-----------|
| `skill` *(default)* | `GODMODE_MODE=skill` | Runs inside Claude Desktop. No cloud API keys needed. Low-quality results flagged `NEEDS REVIEW`. |
| `standalone` | `GODMODE_MODE=standalone` | Runs independently. Low-quality results escalate to cloud automatically. |

---

## Routing pipeline

```
Your prompt
  → L1 Router   classify intent · resolve capabilities · select model
                complexity gate: danger keywords escalate before execution
  → L2 Executor run selected model (streams tokens live)
                quality gate: judge scores output 0–1
                < 0.55 → NEEDS REVIEW (skill) or cloud retry (standalone)
  → L3 Governor optional cloud validation for arch/spec tasks
```

## Intent → model routing

| Intent prefix | Routes to | Examples |
|---|---|---|
| `Utility.*` | local fast model | summarise, classify, extract |
| `Improve.Code` / `Review.Code` | local code model | refactor, review PR |
| `Fix.Bug` / `Review.Security` | cloud or flagged | security audit, crash fix |
| `Architecture.*` | cloud or flagged | system design, ADR |
| `Multimodal.*` | vision model | UI screenshot analysis |

## Source

https://github.com/ronjunevaldoz/godmode
