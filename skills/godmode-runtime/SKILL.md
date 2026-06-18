---
name: godmode-runtime
description: "Godmode runtime skill — use for any task that involves the godmode CLI or AI routing runtime. Covers: routing a prompt through godmode (python3 godmode_cli.py run), file-based code review with the --file flag to prevent model hallucinations, multi-turn sessions via --session, viewing token savings vs Claude Opus (stats command), configuring the Ollama server address, debugging NEEDS REVIEW quality warnings, adjusting routing thresholds or model registry assignments, running the godmode eval suite, or resetting memory. Invoke whenever the user mentions 'godmode', 'godmode_cli', '--file flag', 'NEEDS REVIEW', model routing, or local-first AI cost savings."
---

# Godmode Runtime

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
python3 godmode_cli.py preset apply auto                  # Auto-select preset from RAM
python3 godmode_cli.py recommend                          # Suggest registry improvements
python3 godmode_cli.py recommend --apply                  # Apply recommendations
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
