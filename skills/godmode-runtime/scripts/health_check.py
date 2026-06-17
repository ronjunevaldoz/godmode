#!/usr/bin/env python3
"""
Pre-flight health check for the godmode runtime.
Run before any godmode_cli.py session to catch missing keys or config drift.
"""
import os
import sys
import yaml
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

CHECKS = []

def check(label: str):
    def decorator(fn):
        CHECKS.append((label, fn))
        return fn
    return decorator


@check("ANTHROPIC_API_KEY set")
def _anthropic_key():
    return bool(os.getenv("ANTHROPIC_API_KEY"))


@check("OPENAI_API_KEY set")
def _openai_key():
    return bool(os.getenv("OPENAI_API_KEY"))


@check("GOOGLE_API_KEY set")
def _google_key():
    return bool(os.getenv("GOOGLE_API_KEY"))


@check("model_registry.yaml readable")
def _registry():
    path = os.path.join(ROOT, "configs", "model_registry.yaml")
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return "models" in data
    except Exception:
        return False


@check("intent_map.json readable")
def _intent_map():
    path = os.path.join(ROOT, "routing", "intent_map.json")
    return os.path.isfile(path)


@check("Ollama reachable")
def _ollama():
    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/").replace("/api/chat", "")
    try:
        r = requests.get(base, timeout=3)
        return r.status_code < 500
    except Exception:
        return False


def main():
    passed = failed = 0
    for label, fn in CHECKS:
        ok = fn()
        status = "✓" if ok else "✗"
        print(f"  {status}  {label}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{passed}/{passed + failed} checks passed")
    if failed:
        print("Fix the above before running godmode_cli.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
