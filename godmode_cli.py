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
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "--cov", "--cov-report=term-missing", "-q"],
        capture_output=False,
    )
    sys.exit(result.returncode)


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
    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
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
    "preset":    (cmd_preset,    "Model presets by RAM tier  [list|show|apply <tier|auto>]"),
    "recommend": (cmd_recommend, "Dynamic model recommendations  [--apply to patch registry]"),
    "coverage":  (cmd_coverage,  "Run test suite with line coverage report"),
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
