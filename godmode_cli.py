#!/usr/bin/env python3
"""Godmode CLI — AI routing runtime with local-first cost savings."""

import json
import sys
from pathlib import Path


def cmd_run(args: list[str]) -> None:
    if not args:
        print("Usage: python3 godmode_cli.py run 'your prompt'")
        sys.exit(1)
    from main import orchestrate
    orchestrate(" ".join(args))


def cmd_stats(_args: list[str]) -> None:
    from memory.memory_manager import MemoryManager
    from metrics.metrics_engine import MetricsEngine
    print(MetricsEngine(MemoryManager()).generate_report())


def cmd_eval(_args: list[str]) -> None:
    from evaluation.run_routing_eval import run_eval
    run_eval()


def cmd_clear(_args: list[str]) -> None:
    log_path = Path("memory/task_logs.json")
    log_path.write_text("[]")
    print("✓ Memory cleared.")


def cmd_recommend(args: list[str]) -> None:
    """Show system-aware model recommendations. Pass --apply to patch the registry."""
    from routing.model_recommender import generate_report, patch_registry
    print(generate_report())
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


def cmd_models(_args: list[str]) -> None:
    """Show all local Ollama models and their assigned roles."""
    import requests, os
    base = os.getenv("OLLAMA_BASE_URL", "https://ron-local-home.duckdns.org/ollama")
    base = base.replace("/api/chat", "")
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


COMMANDS = {
    "run":       (cmd_run,       "Route and execute a prompt"),
    "stats":     (cmd_stats,     "Token savings and routing dashboard"),
    "eval":      (cmd_eval,      "Run routing accuracy evaluation"),
    "clear":     (cmd_clear,     "Reset memory / task logs"),
    "models":    (cmd_models,    "List Ollama models and their roles"),
    "recommend": (cmd_recommend, "System-aware model recommendations  [--apply to patch registry]"),
}


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("\n  godmode_cli.py <command> [args]\n")
        for name, (_, desc) in COMMANDS.items():
            print(f"    {name:<10} {desc}")
        print()
        return

    cmd = args[0]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd!r}. Run with --help.")
        sys.exit(1)

    COMMANDS[cmd][0](args[1:])


if __name__ == "__main__":
    main()
