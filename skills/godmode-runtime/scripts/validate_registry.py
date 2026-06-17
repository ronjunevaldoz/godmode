#!/usr/bin/env python3
"""
Cross-validates model_registry.yaml against intent_map.json.
Catches capability drift: capabilities referenced in intent_map but absent
from every model in the registry, and enabled models with empty capability lists.
"""
import json
import os
import sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def load():
    with open(os.path.join(ROOT, "configs", "model_registry.yaml")) as f:
        registry = yaml.safe_load(f)
    with open(os.path.join(ROOT, "routing", "intent_map.json")) as f:
        intent_map = json.load(f)
    return registry, intent_map


def validate(registry: dict, intent_map: dict) -> list[str]:
    errors: list[str] = []
    models = registry.get("models", {})

    # All capabilities across enabled models
    all_caps: set[str] = set()
    for model_id, meta in models.items():
        if not meta.get("enabled", False):
            continue
        caps = meta.get("capabilities", [])
        if not caps:
            errors.append(f"Model '{model_id}' is enabled but has no capabilities")
        all_caps.update(caps)

    # All capabilities required by intents
    required_caps: set[str] = set()
    for intent, caps in intent_map.items():
        required_caps.update(caps)

    # Capabilities required but not covered by any model
    uncovered = required_caps - all_caps
    for cap in sorted(uncovered):
        errors.append(f"Capability '{cap}' is required by intent_map but no enabled model provides it")

    return errors


def main():
    try:
        registry, intent_map = load()
    except Exception as e:
        print(f"  ✗  Failed to load config files: {e}")
        sys.exit(1)

    errors = validate(registry, intent_map)
    if errors:
        print("Registry validation FAILED:\n")
        for err in errors:
            print(f"  ✗  {err}")
        sys.exit(1)
    else:
        models = registry.get("models", {})
        enabled = sum(1 for m in models.values() if m.get("enabled"))
        print(f"  ✓  Registry valid — {enabled} enabled models, all intent capabilities covered")


if __name__ == "__main__":
    main()
