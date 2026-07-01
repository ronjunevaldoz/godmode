#!/usr/bin/env python3
"""Godmode CLI — AI routing runtime with local-first cost savings."""

import json
import sys
from pathlib import Path
from version import __version__

# Load .env.local then .env (first found wins per key)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env.local", override=False)
    load_dotenv(Path(__file__).parent / ".env", override=False)
except ImportError:
    pass


def cmd_run(args: list[str]) -> None:
    session: str | None = None
    files: list[str] = []

    # Parse flags, collect remaining args as the prompt
    prompt_parts: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--session" and i + 1 < len(args):
            session = args[i + 1]
            i += 2
        elif args[i] == "--file" and i + 1 < len(args):
            files.append(args[i + 1])
            i += 2
        else:
            prompt_parts.append(args[i])
            i += 1

    if not prompt_parts:
        print("Usage: python3 godmode_cli.py run 'prompt' [--file path] [--session name]")
        print("       --file can be repeated for multiple files")
        sys.exit(1)

    from main import orchestrate
    orchestrate(" ".join(prompt_parts), session=session, files=files or None)


def cmd_stats(_args: list[str]) -> None:
    from memory.memory_manager import MemoryManager
    from metrics.metrics_engine import MetricsEngine
    print(MetricsEngine(MemoryManager()).generate_report())


def cmd_eval(_args: list[str]) -> None:
    from evaluation.run_routing_eval import run_eval
    run_eval()


def cmd_benchmark(args: list[str]) -> None:
    """Run a small local model benchmark across the available Ollama models."""
    from evaluation.model_benchmark import run_benchmark, render_report, DEFAULT_MODEL_IDS
    from routing.model_recommender import _missing_ollama_entries, pull_models

    model_ids = DEFAULT_MODEL_IDS
    if "--pull" in args:
        missing = _missing_ollama_entries()
        if missing:
            print("Pulling missing models before benchmark:\n")
            for entry in missing:
                print(f"  {entry['model_id']:<22} → {entry['model']}")
            print()
            pull_models([entry["model"] for entry in missing])

    if "--models" in args:
        idx = args.index("--models")
        if idx + 1 < len(args):
            model_ids = [m.strip() for m in args[idx + 1].split(",") if m.strip()]

    benchmark = run_benchmark(model_ids=model_ids)
    print(render_report(benchmark))


def cmd_clear(_args: list[str]) -> None:
    log_path = Path("memory/task_logs.json")
    log_path.write_text("[]")
    print("✓ Memory cleared.")


def cmd_preset(args: list[str]) -> None:
    """
    Manage model presets.
      preset list              — show tier matrix
      preset show <tier>       — show what a tier sets (dry run)
      preset apply <tier>      — patch model_registry.yaml
      preset apply auto        — auto-select tier from OLLAMA_SERVER_RAM_GB
    """
    from routing.preset_manager import (
        generate_matrix, list_presets, get_preset,
        apply_preset, auto_select_tier,
    )
    from routing.model_recommender import _get_server_ram_gb, _get_pulled_models

    sub = args[0] if args else "list"

    if sub == "list":
        print(generate_matrix())
        return

    if sub in ("show", "apply"):
        if len(args) < 2:
            print(f"Usage: godmode_cli.py preset {sub} <tier|auto>")
            return

        tier = args[1]
        if tier == "auto":
            pulled   = _get_pulled_models()
            ram, src = _get_server_ram_gb(pulled)
            tier     = auto_select_tier(ram)
            print(f"  Server RAM ~{ram:.0f} GB ({src}) → selecting tier: {tier}\n")

        preset = get_preset(tier)
        if not preset:
            print(f"Unknown tier '{tier}'. Run 'preset list' to see options.")
            return

        dry = (sub == "show")
        changes = apply_preset(tier, dry_run=dry)

        action = "Would change" if dry else "Applied"
        print(f"  Preset: {preset['label']} — {preset['description']}\n")
        if changes:
            print(f"  {action}:")
            for c in changes:
                print(c)
        else:
            print("  No changes — registry already matches this preset.")
        print()

        if not dry:
            # Show pull commands for any model not yet on the server
            from routing.model_recommender import _get_pulled_models
            pulled_names = {m["name"] for m in _get_pulled_models()}
            missing = [
                info["model"]
                for info in preset["roles"].values()
                if info["model"] not in pulled_names
            ]
            if missing:
                print("  Models not yet pulled on server:")
                for m in missing:
                    print(f"    ollama pull {m}")
                print()
        return

    print(f"Unknown subcommand '{sub}'. Use: list | show <tier> | apply <tier|auto>")


def cmd_coverage(_args: list[str]) -> None:
    """Run test suite with coverage and print the term-missing report."""
    import subprocess
    # Hardcoded args — no user input reaches subprocess.run
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "--cov", "--cov-report=term-missing", "-q"],
        capture_output=False,
    )
    sys.exit(result.returncode)


def cmd_recommend(args: list[str]) -> None:
    """Show system-aware model recommendations. Pass --apply to patch the registry."""
    from routing.model_recommender import (
        generate_report,
        patch_registry,
        generate_model_research_report,
        _missing_ollama_entries,
        pull_models,
    )
    print(generate_report())
    if "--pull" in args:
        print(generate_model_research_report())
        missing = _missing_ollama_entries()
        if missing:
            print("  Pulling missing models now:\n")
            results = pull_models([entry["model"] for entry in missing])
            for model_name, status in results.items():
                print(f"  {model_name:<35} {status}")
            print()
        else:
            print("  No missing Ollama registry models to pull.\n")
    if "--apply" in args:
        changes = patch_registry(dry_run=False)
        if changes:
            print("  Applied changes to model_registry.yaml:")
            for c in changes:
                print(c)
            print()
        else:
            print("  No changes needed — registry already optimal.\n")
    else:
        changes = patch_registry(dry_run=True)
        if changes:
            print("  Suggested registry changes (run with --apply to patch):")
            for c in changes:
                print(c)
            print()


def cmd_session(args: list[str]) -> None:
    """
    Manage multi-turn conversation sessions.
      session list              — list all saved sessions
      session show <name>       — print full history for a session
      session clear <name>      — delete a session
    """
    from memory.session_manager import SessionManager
    sm = SessionManager()
    sub = args[0] if args else "list"

    if sub == "list":
        sessions = sm.list_sessions()
        if not sessions:
            print("\n  No sessions yet. Start one with:  run 'prompt' --session <name>\n")
            return
        print(f"\n  {'Session':<24} Turns")
        print("  " + "─" * 36)
        for name in sessions:
            print(f"  {name:<24} {sm.turn_count(name)}")
        print()

    elif sub == "show":
        if len(args) < 2:
            print("Usage: godmode_cli.py session show <name>")
            return
        name = args[1]
        history = sm.load(name)
        if not history:
            print(f"  Session {name!r} not found or empty.")
            return
        print(f"\n  Session: {name!r}\n")
        for msg in history:
            role = msg["role"].upper()
            print(f"  [{role}]\n  {msg['content']}\n")

    elif sub == "clear":
        if len(args) < 2:
            print("Usage: godmode_cli.py session clear <name>")
            return
        name = args[1]
        if sm.clear(name):
            print(f"  ✓ Session {name!r} cleared.")
        else:
            print(f"  Session {name!r} not found.")

    else:
        print(f"Unknown subcommand '{sub}'. Use: list | show <name> | clear <name>")


def cmd_setup(_args: list[str]) -> None:
    """Interactive first-run setup wizard."""
    from setup_wizard import run
    run()


def cmd_models(_args: list[str]) -> None:
    """Show local Ollama models, registry research, or pull missing models."""
    import requests, os

    sub = _args[0] if _args else "list"
    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    base = base.replace("/api/chat", "")

    if sub == "research":
        from routing.model_recommender import generate_model_research_report
        print(generate_model_research_report())
        return

    if sub == "pull":
        from routing.model_recommender import (
            _missing_ollama_entries,
            _registry_ollama_entries,
            pull_models,
            enable_registry_models,
        )

        explicit_ids = _args[1:]
        if explicit_ids:
            registry_entries = {e["model_id"]: e for e in _registry_ollama_entries(include_disabled=True)}
            targets = [registry_entries[mid] for mid in explicit_ids if mid in registry_entries]
        else:
            targets = _missing_ollama_entries()

        if not targets:
            print("No matching Ollama registry models found.")
            return

        print("\n  Pulling missing Ollama registry models:\n")
        for entry in targets:
            print(f"  {entry['model_id']:<22} → {entry['model']}")
        print()

        results = pull_models([entry["model"] for entry in targets])
        for model_name, status in results.items():
            print(f"  {model_name:<35} {status}")
        print()

        if explicit_ids:
            updated = enable_registry_models([
                entry["model_id"]
                for entry in targets
                if not str(results.get(entry["model"], "")).startswith("error")
            ])
            if updated:
                print("  Enabled registry models:")
                for model_id in updated:
                    print(f"    {model_id}")
                print()
        return

    if sub not in ("list", ""):
        print("Usage: godmode_cli.py models [list|research|pull]")
        return

    try:
        data = requests.get(f"{base}/api/tags", timeout=5).json()
    except Exception as e:
        print(f"Cannot reach Ollama: {e}")
        return

    from agents.ollama_utility import LOCAL_MODEL_ROLES as ROLES
    print("\n  Available Ollama models:\n")
    print(f"  {'Model':<30} {'Size':>6}   Role")
    print("  " + "─" * 65)
    for m in data.get("models", []):
        name = m["name"]
        size = f"{m.get('size', 0) / 1e9:.1f}GB"
        role = ROLES.get(name, "—")
        tag  = " ◀ assigned" if role != "—" else ""
        print(f"  {name:<30} {size:>6}   {role}{tag}")
    print()


def cmd_report(_args: list[str]) -> None:
    from collections import defaultdict

    log_path = Path(__file__).parent / "logs" / "failures.jsonl"
    if not log_path.exists():
        print("\n  No failure log yet — logs/failures.jsonl is created on first flagged run.\n")
        return

    entries: list[dict] = []
    with log_path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    if not entries:
        print("\n  Failure log is empty.\n")
        return

    by_intent: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_intent[e.get("intent", "unknown")].append(e)

    print(f"\n{'═' * 60}")
    print(f"  Godmode Failure Report  ({len(entries)} flagged runs)")
    print(f"{'═' * 60}\n")

    for intent, runs in sorted(by_intent.items(), key=lambda x: -len(x[1])):
        scores = [r["score"] for r in runs if r.get("score") is not None]
        avg    = sum(scores) / len(scores) if scores else 0.0
        models = {r["model"] for r in runs}
        reasons = [r.get("reason", "") for r in runs]
        top_reason = max(set(reasons), key=reasons.count) if any(reasons) else "—"

        print(f"  {intent}")
        print(f"    runs={len(runs)}  avg_score={avg:.2f}  models={', '.join(models)}")
        print(f"    top reason: {top_reason}")

        # Show most recent prompt excerpt
        last = runs[-1]
        excerpt = last.get("prompt", "")[:120].replace("\n", " ")
        print(f"    last prompt: {excerpt!r}")
        print()

    print(f"  Tip: intents with avg_score < 0.40 need a stronger model assignment.")
    print(f"  Run: python3 godmode_cli.py recommend\n")


COMMANDS = {
    "setup":     (cmd_setup,     "First-run setup wizard — configure Ollama and assign models"),
    "run":       (cmd_run,       "Route and execute a prompt  [--file path] [--session name]"),
    "session":   (cmd_session,   "Manage conversation sessions  [list|show <name>|clear <name>]"),
    "stats":     (cmd_stats,     "Token savings and routing dashboard"),
    "report":    (cmd_report,    "Show flagged-run failure log grouped by intent"),
    "eval":      (cmd_eval,      "Run routing accuracy evaluation"),
    "benchmark": (cmd_benchmark, "Compare local models on a small prompt suite  [--models a,b,c] [--pull]"),
    "clear":     (cmd_clear,     "Reset memory / task logs"),
    "models":    (cmd_models,    "List Ollama models, research registry targets, or pull missing ones  [list|research|pull]"),
    "preset":    (cmd_preset,    "Model presets by RAM tier  [list|show|apply <tier|auto>]"),
    "recommend": (cmd_recommend, "Dynamic model recommendations  [--apply to patch registry|--pull missing Ollama models]"),
    "coverage":  (cmd_coverage,  "Run test suite with line coverage report"),
}


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(f"\n  godmode v{__version__} — local-first AI routing runtime\n")
        print("  Usage: godmode_cli.py <command> [args]\n")
        for name, (_, desc) in COMMANDS.items():
            print(f"    {name:<10} {desc}")
        print()
        return
    if args[0] in ("-v", "--version"):
        print(f"godmode v{__version__}")
        return

    cmd = args[0]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd!r}. Run with --help.")
        sys.exit(1)

    COMMANDS[cmd][0](args[1:])


if __name__ == "__main__":
    main()
