"""
Preset manager: applies curated role→model assignments from model_presets.yaml
to model_registry.yaml based on server RAM tier.
"""

import logging
import os
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent

PRESETS_PATH  = ROOT / "configs" / "model_presets.yaml"
REGISTRY_PATH = ROOT / "configs" / "model_registry.yaml"


def _load_presets() -> dict:
    with open(PRESETS_PATH) as f:
        return yaml.safe_load(f)


def _load_registry() -> dict:
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)


def list_presets() -> list[dict]:
    """Return all tiers as a list of {id, label, description, min_ram_gb, roles}."""
    data = _load_presets()
    result = []
    for tier_id, info in data.get("presets", {}).items():
        result.append({
            "id":          tier_id,
            "label":       info["label"],
            "description": info["description"],
            "min_ram_gb":  info["min_ram_gb"],
            "roles":       info["roles"],
        })
    return sorted(result, key=lambda x: x["min_ram_gb"])


def get_preset(tier_id: str) -> dict | None:
    data = _load_presets()
    return data.get("presets", {}).get(tier_id)


def auto_select_tier(server_ram_gb: float) -> str:
    """Return the best tier ID for the given server RAM."""
    presets = _load_presets().get("presets", {})
    best_tier = None
    best_ram  = 0
    for tier_id, info in presets.items():
        min_ram = info.get("min_ram_gb", 0)
        if min_ram <= server_ram_gb and min_ram >= best_ram:
            best_ram  = min_ram
            best_tier = tier_id
    return best_tier or "8gb"


def apply_preset(tier_id: str, dry_run: bool = False) -> list[str]:
    """
    Patch model_registry.yaml with the models from the given tier.
    Returns a list of change strings. If dry_run=True nothing is written.
    """
    preset = get_preset(tier_id)
    if not preset:
        raise ValueError(f"Unknown preset tier: {tier_id!r}. Run 'preset list' to see options.")

    registry = _load_registry()
    models   = registry.get("models", {})
    changes  = []

    for registry_id, role_info in preset["roles"].items():
        if registry_id not in models:
            changes.append(f"  SKIP {registry_id} — not in registry")
            continue

        new_model = role_info["model"]
        current   = models[registry_id].get("model", "")
        new_role  = role_info.get("role", models[registry_id].get("role", ""))

        if current != new_model:
            changes.append(f"  {registry_id:<22} {current}  →  {new_model}")
            if not dry_run:
                models[registry_id]["model"] = new_model
                models[registry_id]["role"]  = new_role

    if not dry_run and changes:
        with open(REGISTRY_PATH, "w") as f:
            yaml.dump(registry, f, default_flow_style=False, sort_keys=False)

    return changes


def generate_matrix() -> str:
    """Render a full tier × role matrix for display."""
    presets = _load_presets().get("presets", {})
    tiers   = sorted(presets.items(), key=lambda x: x[1]["min_ram_gb"])

    # Collect all role IDs in order
    role_ids = list(next(iter(presets.values()))["roles"].keys())

    col_w  = 30
    tier_w = 14

    header = f"  {'Role':<22}" + "".join(f"{t[1]['label']:<{tier_w}}" for t in tiers)
    divider = "  " + "─" * (22 + tier_w * len(tiers))

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════════════════╗",
        "║                  Godmode Model Preset Matrix                            ║",
        "╚══════════════════════════════════════════════════════════════════════════╝",
        "",
        header,
        divider,
    ]

    for role_id in role_ids:
        role_label = role_id.replace("ollama_", "").replace("_", " ")
        row = f"  {role_label:<22}"
        for _, info in tiers:
            model = info["roles"].get(role_id, {}).get("model", "—")
            # Shorten for display: strip version tag if long
            short = model.split(":")[0] if len(model) > tier_w - 2 else model
            row += f"{short:<{tier_w}}"
        lines.append(row)

    lines += [
        divider,
        "",
        "  Tiers:",
    ]
    for tier_id, info in tiers:
        lines.append(f"    {tier_id:<8} {info['label']:<20} {info['description']}")

    lines.append("")
    return "\n".join(lines)
