#!/usr/bin/env python3
"""
Godmode first-run setup wizard.
Detects Ollama, maps pulled models to roles, and writes .env.local.
"""

import os
import sys
import yaml
import requests
from pathlib import Path

ROOT = Path(__file__).parent
ENV_LOCAL = ROOT / ".env.local"
REGISTRY_PATH = ROOT / "configs" / "model_registry.yaml"

# Role → registry key mapping
ROLE_KEYS = {
    "Code review / bug fix / tests":       "ollama_qwen_coder",
    "Security audit / deep reasoning":     "ollama_deepseek",
    "Research / docs / analysis":          "ollama_gemma",
    "Long-context research / reasoning":    "ollama_qwythos",
    "Fast assistant / classification":     "ollama_qwen_fast",
    "Vision / UI screenshots":             "ollama_llava",
}

# Keyword hints to auto-suggest a role for a pulled model
ROLE_HINTS: list[tuple[list[str], str]] = [
    (["llava", "vision", "moondream", "bakllava"],       "Vision / UI screenshots"),
    (["qwythos", "mythos"],                               "Long-context research / reasoning"),
    (["deepseek", "r1"],                                  "Security audit / deep reasoning"),
    (["coder", "codestral", "starcoder", "qwen2.5-coder","qwen3-coder"], "Code review / bug fix / tests"),
    (["gemma", "mistral", "phi", "llama"],                "Research / docs / analysis"),
    (["qwen", "tinyllama", "smollm", "orca-mini"],        "Fast assistant / classification"),
]


def _color(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text

def ok(t):  return _color(t, "32")
def warn(t): return _color(t, "33")
def err(t):  return _color(t, "31")
def bold(t): return _color(t, "1")
def dim(t):  return _color(t, "2")


def _ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        val = input(f"  {prompt}{hint}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        sys.exit(0)
    return val or default


def _fetch_models(base_url: str) -> list[dict] | None:
    base = base_url.rstrip("/").replace("/api/chat", "")
    try:
        r = requests.get(f"{base}/api/tags", timeout=6)
        r.raise_for_status()
        return r.json().get("models", [])
    except requests.ConnectionError:
        return None
    except Exception as e:
        print(warn(f"  Warning: {e}"))
        return None


def _guess_role(model_name: str) -> str:
    name = model_name.lower()
    for keywords, role in ROLE_HINTS:
        if any(k in name for k in keywords):
            return role
    return "Fast assistant / classification"


def _patch_registry(assignments: dict[str, str]) -> None:
    """Write ollama_model values into model_registry.yaml."""
    with open(REGISTRY_PATH) as f:
        data = yaml.safe_load(f)
    for registry_key, model_name in assignments.items():
        if registry_key in data.get("models", {}):
            data["models"][registry_key]["model"] = model_name
    with open(REGISTRY_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def _write_env(url: str, mode: str, ram_gb: str) -> None:
    lines = [
        f"OLLAMA_BASE_URL={url}",
        f"GODMODE_MODE={mode}",
    ]
    if ram_gb:
        lines.append(f"OLLAMA_SERVER_RAM_GB={ram_gb}")
    ENV_LOCAL.write_text("\n".join(lines) + "\n")


def run() -> None:
    print()
    print(bold("  ╔══════════════════════════════════════════════╗"))
    print(bold("  ║        Godmode  —  First-run Setup          ║"))
    print(bold("  ╚══════════════════════════════════════════════╝"))
    print()

    # ── 1. Ollama URL ─────────────────────────────────────────────────────────
    existing_url = os.getenv("OLLAMA_BASE_URL", "")
    if ENV_LOCAL.exists():
        for line in ENV_LOCAL.read_text().splitlines():
            if line.startswith("OLLAMA_BASE_URL="):
                existing_url = line.split("=", 1)[1].strip()
    default_url = existing_url or "http://localhost:11434"

    print(bold("  Step 1 — Ollama server"))
    url = _ask("Ollama base URL", default_url)
    url = url.rstrip("/").replace("/api/chat", "")

    print(f"  Connecting to {dim(url)} …", end=" ", flush=True)
    models = _fetch_models(url)
    if models is None:
        print(err("✗ unreachable"))
        print(warn("  Cannot reach Ollama. Check the URL and try again."))
        print(warn("  Tip: for a remote server use https://your-host/ollama"))
        ans = _ask("Save URL anyway and continue? (y/n)", "n")
        if ans.lower() != "y":
            sys.exit(1)
        models = []
    else:
        print(ok(f"✓  {len(models)} model(s) found"))

    # ── 2. RAM hint ───────────────────────────────────────────────────────────
    print()
    print(bold("  Step 2 — Server RAM (for preset recommendations)"))
    print(dim("  Leave blank to auto-detect from loaded models."))
    ram_gb = _ask("Server RAM in GB", "")

    # ── 3. Model → role assignments ───────────────────────────────────────────
    assignments: dict[str, str] = {}   # registry_key → model_name
    if models:
        print()
        print(bold("  Step 3 — Assign models to roles"))
        print(dim("  Press Enter to accept the suggested role, or type a number to pick.\n"))
        roles = list(ROLE_KEYS.keys())

        for m in models:
            name = m["name"]
            size_gb = m.get("size", 0) / 1e9
            suggested = _guess_role(name)
            print(f"  {bold(name)} ({size_gb:.1f} GB)")
            for i, role in enumerate(roles, 1):
                marker = ok("→") if role == suggested else " "
                print(f"    {marker} {i}. {role}")
            choice = _ask("Role number (Enter = suggested, 0 = skip)", "")
            if choice == "0":
                continue
            if choice.isdigit() and 1 <= int(choice) <= len(roles):
                selected = roles[int(choice) - 1]
            else:
                selected = suggested
            registry_key = ROLE_KEYS[selected]
            # Last assignment wins if multiple models target the same role
            assignments[registry_key] = name
            print(f"    {ok('✓')} {name}  →  {selected}\n")
    else:
        print()
        print(warn("  Step 3 — Skipped (no models detected)"))
        print(dim("  Pull models with:  ollama pull qwen3:8b"))

    # ── 4. Mode ───────────────────────────────────────────────────────────────
    print()
    print(bold("  Step 4 — Operating mode"))
    print("    1. skill      Use inside Claude Desktop (no cloud API keys needed)  ← default")
    print("    2. standalone Run independently with cloud escalation active")
    mode_choice = _ask("Mode (1 or 2)", "1")
    mode = "standalone" if mode_choice == "2" else "skill"

    # ── 5. Write config ───────────────────────────────────────────────────────
    print()
    print(bold("  Step 5 — Writing config"))
    _write_env(url, mode, ram_gb)
    print(f"  {ok('✓')} Wrote {ENV_LOCAL.relative_to(ROOT)}")

    if assignments:
        _patch_registry(assignments)
        print(f"  {ok('✓')} Patched configs/model_registry.yaml ({len(assignments)} role(s))")

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print(bold("  ══════════════════════════════════════════════"))
    print(bold("  Setup complete! Next steps:"))
    print()
    print(f"    python3 godmode_cli.py run \"hello\"    {dim('# test routing')}")
    print(f"    python3 godmode_cli.py stats           {dim('# usage dashboard')}")
    print(f"    python3 godmode_cli.py preset list     {dim('# RAM-tiered model presets')}")
    print()
    if not assignments and models:
        print(warn("  Note: no roles were assigned — routing will use registry defaults."))
        print(dim("  Run 'python3 godmode_cli.py recommend' to get suggestions."))
        print()


if __name__ == "__main__":
    run()
