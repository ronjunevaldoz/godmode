"""
Server-aware Ollama model recommender.

Queries Ollama for pulled models and scores each per role.
Set OLLAMA_SERVER_RAM_GB in your environment to match the dedicated
server's RAM (or VRAM for GPU servers). Without it the recommender
falls back to probing the largest loaded model as a lower-bound estimate.
"""

import logging
import os
from pathlib import Path

import yaml
import requests

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent

OLLAMA_BASE_URL: str = os.getenv(
    "OLLAMA_BASE_URL", "http://localhost:11434"
).replace("/api/chat", "")

REGISTRY_PATH = ROOT / "configs" / "model_registry.yaml"

# Set OLLAMA_SERVER_RAM_GB to your dedicated server's usable RAM/VRAM in GB.
# Example in .env:  OLLAMA_SERVER_RAM_GB=48
_SERVER_RAM_ENV = os.getenv("OLLAMA_SERVER_RAM_GB")

# How much RAM to reserve for the Ollama daemon + OS overhead on the server
OS_OVERHEAD_GB = 4.0

# Comfort bands — model must fit within available RAM at these ratios
# "safe"    → model ≤ 80% of available (leaves headroom for context)
# "tight"   → model ≤ 95% (usable but context window may be limited)
# "swap"    → model > available (will use swap — avoid for latency-sensitive roles)
SAFE_RATIO  = 0.80
TIGHT_RATIO = 0.95

# Role → keywords that score positively when found in the model name
ROLE_AFFINITY: dict[str, list[str]] = {
    "code_review":    ["coder", "code", "qwen", "deepseek"],
    "unit_test":      ["coder", "code", "qwen"],
    "bug_fix":        ["coder", "code", "deepseek", "r1"],
    "security_audit": ["deepseek", "r1", "qwen", "hermes"],
    "research":       ["qwythos", "mythos", "gemma", "llama", "qwen", "hermes"],
    "prompt_quality": ["deepseek", "r1", "hermes", "qwen"],
    "code_improvement": ["coder", "code", "qwen"],
    "assistant":      ["qwen", "llama", "gemma"],
    "vision":         ["llava", "moondream", "gemma4", "bakllava"],
    "classification": ["qwen", "llama", "gemma"],
    "summarization":  ["gemma", "llama", "qwen"],
    "documentation":  ["gemma", "llama", "qwen"],
}

# Roles that benefit from larger models (penalise tiny ones)
QUALITY_SENSITIVE = {"security_audit", "bug_fix", "code_review", "prompt_quality"}

# Roles where speed matters more than size
SPEED_SENSITIVE = {"assistant", "classification", "summarization"}


def _get_server_ram_gb(pulled: list[dict]) -> tuple[float, str]:
    """
    Return (ram_gb, source) for the Ollama server.

    Priority:
      1. OLLAMA_SERVER_RAM_GB env var (user-configured, most accurate)
      2. /api/ps  — Ollama's "running models" endpoint exposes size_vram
         if a model is currently loaded; we can infer minimum capacity
      3. Largest pulled model × 1.25 as a conservative lower-bound guess
    """
    if _SERVER_RAM_ENV:
        return float(_SERVER_RAM_ENV), f"OLLAMA_SERVER_RAM_GB={_SERVER_RAM_ENV}"

    # /api/ps only shows one loaded model's VRAM — always an underestimate, skip it.
    # Instead: the largest model you've successfully pulled must fit in server RAM,
    # so use it as a lower-bound and add a 25% headroom factor.
    if pulled:
        largest = max(m["size_gb"] for m in pulled)
        estimate = largest / 0.75
        return estimate, f"estimated ≥ {largest:.1f} GB (largest pulled model × 1.25 headroom)"

    return 32.0, "default fallback — set OLLAMA_SERVER_RAM_GB for accuracy"


def _get_pulled_models() -> list[dict]:
    """Return list of {name, size_gb} for models already in Ollama."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        return [
            {"name": m["name"], "size_gb": m.get("size", 0) / 1e9}
            for m in models
        ]
    except Exception as e:
        logger.warning(f"Could not reach Ollama: {e}")
        return []


def _load_registry() -> dict:
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)


def _enabled_ollama_entries() -> list[dict]:
    """Return enabled registry entries that are backed by Ollama."""
    return _registry_ollama_entries(include_disabled=False)


def _registry_ollama_entries(include_disabled: bool = True) -> list[dict]:
    """Return Ollama registry entries, optionally including disabled ones."""
    registry = _load_registry()
    results: list[dict] = []
    for model_id, meta in registry.get("models", {}).items():
        if meta.get("provider") != "ollama":
            continue
        if not include_disabled and not meta.get("enabled", False):
            continue
        results.append({
            "model_id": model_id,
            "model": meta.get("model", ""),
            "role": meta.get("role", ""),
            "capabilities": meta.get("capabilities", []),
            "enabled": meta.get("enabled", False),
        })
    return results


def _missing_ollama_entries() -> list[dict]:
    """Return enabled Ollama entries that are not currently pulled."""
    pulled = {m["name"] for m in _get_pulled_models()}
    return [
        entry for entry in _enabled_ollama_entries()
        if entry["model"] not in pulled
    ]


def _experimental_ollama_entries() -> list[dict]:
    """Return disabled Ollama registry entries."""
    return [
        entry for entry in _registry_ollama_entries(include_disabled=True)
        if not entry.get("enabled", False)
    ]


def get_model_research() -> dict[str, dict]:
    """
    Return registry-driven recommendations for enabled Ollama-backed models.

    Each entry includes whether the model is already pulled locally.
    """
    pulled = {m["name"] for m in _get_pulled_models()}
    research: dict[str, dict] = {}
    for entry in _registry_ollama_entries(include_disabled=True):
        model_name = entry["model"]
        research[entry["model_id"]] = {
            **entry,
            "pulled": model_name in pulled,
        }
    return research


def generate_model_research_report() -> str:
    research = get_model_research()
    pulled_names = {info["model"] for info in research.values() if info["pulled"]}

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════╗",
        "║          Godmode Model Research & Pull Report            ║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
        "  Ollama-backed registry models:",
    ]

    for entry in _registry_ollama_entries(include_disabled=True):
        model = entry["model"]
        badge = "✓" if model in pulled_names else "✗"
        status = "pulled" if model in pulled_names else "missing"
        if not entry.get("enabled", False):
            status = f"disabled, {status}"
        lines.append(
            f"    {badge} {entry['model_id']:<22} {model:<20} "
            f"[{status}]  role={entry['role']}"
        )

    missing = _missing_ollama_entries()
    lines += ["", f"  Missing pulled models: {len(missing)}"]
    if missing:
        for entry in missing:
            lines.append(f"    ollama pull {entry['model']}")
    else:
        lines.append("    None — all enabled Ollama models are already pulled.")

    experimental = _experimental_ollama_entries()
    lines += ["", f"  Disabled experimental models: {len(experimental)}"]
    if experimental:
        for entry in experimental:
            state = "pulled" if entry["model"] in pulled_names else "not pulled"
            lines.append(
                f"    {entry['model_id']:<22} {entry['model']:<20} "
                f"[{state}]  role={entry['role']}"
            )
            if entry["model"] not in pulled_names:
                lines.append(f"      ollama pull {entry['model']}")

    lines += ["", "  Role recommendations (pulled models only):"]
    recs = recommend()
    if recs:
        for role, info in recs.items():
            lines.append(
                f"    {role:<20} → {info['model']:<35} "
                f"{info['size_gb']:>5.1f} GB  ({info['reason']})"
            )
    else:
        lines.append("    No pulled models available yet.")

    lines += [""]
    return "\n".join(lines)


def enable_registry_models(model_ids: list[str]) -> list[str]:
    """Enable the named registry models and persist the registry."""
    if not model_ids:
        return []

    registry = _load_registry()
    updated: list[str] = []
    models = registry.get("models", {})
    for model_id in model_ids:
        if model_id in models and not models[model_id].get("enabled", False):
            models[model_id]["enabled"] = True
            updated.append(model_id)

    if updated:
        with open(REGISTRY_PATH, "w") as f:
            yaml.dump(registry, f, default_flow_style=False, sort_keys=False)
    return updated


def pull_models(model_names: list[str]) -> dict[str, str]:
    """
    Pull the provided Ollama model names using the server's /api/pull endpoint.

    Returns a mapping of model name to final status string.
    """
    if not model_names:
        return {}

    results: dict[str, str] = {}
    pull_url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/pull"
    for model_name in model_names:
        try:
            resp = requests.post(
                pull_url,
                json={"model": model_name, "stream": False},
                timeout=600,
            )
            resp.raise_for_status()
            payload = resp.json()
            results[model_name] = payload.get("status", "success")
        except Exception as e:
            logger.error(f"Failed to pull {model_name}: {e}")
            results[model_name] = f"error: {e}"
    return results


def _fit_band(model_size_gb: float, available_gb: float) -> str:
    ratio = model_size_gb / available_gb if available_gb > 0 else 999
    if ratio <= SAFE_RATIO:
        return "safe"
    if ratio <= TIGHT_RATIO:
        return "tight"
    return "swap"


def _score_model(model: dict, role: str, available_gb: float) -> float:
    name   = model["name"].lower()
    size   = model["size_gb"]
    band   = _fit_band(size, available_gb)

    if band == "swap":
        return -1.0  # never recommend a model that needs swap

    score = 0.0

    # Fit bonus
    score += 30.0 if band == "safe" else 15.0

    # Affinity: score every keyword hit; earlier keywords in the list are worth more
    affinities = ROLE_AFFINITY.get(role, [])
    for i, kw in enumerate(affinities):
        if kw in name:
            score += 15.0 - i * 2.0  # first keyword = +15, second = +13, etc.

    # Size scoring
    if role in QUALITY_SENSITIVE:
        # Larger = better, up to available RAM
        score += min(size, available_gb * SAFE_RATIO) * 1.5
    elif role in SPEED_SENSITIVE:
        # Smaller = faster — reward small models
        score += max(0.0, (available_gb - size)) * 1.0
    else:
        # Balanced — mild preference for larger
        score += min(size, available_gb * SAFE_RATIO) * 0.8

    # Custom / fine-tuned models get a small boost (user explicitly built them)
    if "custom" in name:
        score += 5.0

    return score


def recommend(roles: list[str] | None = None) -> dict[str, dict]:
    """
    For each role, return the best available Ollama model.

    Returns dict: role → {model, size_gb, band, score, reason}
    """
    roles = roles or list(ROLE_AFFINITY.keys())
    pulled = _get_pulled_models()
    if not pulled:
        return {}

    ram_gb, _ = _get_server_ram_gb(pulled)
    available_gb = ram_gb - OS_OVERHEAD_GB

    results: dict[str, dict] = {}
    for role in roles:
        best = None
        best_score = float("-inf")
        for model in pulled:
            s = _score_model(model, role, available_gb)
            if s > best_score:
                best_score = s
                best = model

        if best:
            band = _fit_band(best["size_gb"], available_gb)
            results[role] = {
                "model":   best["name"],
                "size_gb": round(best["size_gb"], 1),
                "band":    band,
                "score":   round(best_score, 1),
                "reason":  _explain(best["name"], role, band),
            }

    return results


def _explain(model: str, role: str, band: str) -> str:
    parts = []
    name = model.lower()
    affinities = ROLE_AFFINITY.get(role, [])
    for kw in affinities:
        if kw in name:
            parts.append(f"affinity:{kw}")
            break
    parts.append(f"fit:{band}")
    if "custom" in name:
        parts.append("fine-tuned")
    return ", ".join(parts)


def generate_report() -> str:
    pulled     = _get_pulled_models()
    ram_gb, ram_source = _get_server_ram_gb(pulled)
    available  = ram_gb - OS_OVERHEAD_GB

    server_url = OLLAMA_BASE_URL.replace("/api/chat", "")
    ram_hint   = "" if _SERVER_RAM_ENV else "  ⚠ Set OLLAMA_SERVER_RAM_GB for accurate fit analysis"

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════╗",
        "║          Godmode Model Recommendation Report             ║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
        f"  Server : {server_url}",
        f"  RAM    : ~{ram_gb:.0f} GB  ({ram_source})",
        f"  Usable : ~{available:.1f} GB  (after {OS_OVERHEAD_GB:.0f} GB server overhead)",
    ]
    if ram_hint:
        lines.append(ram_hint)
    lines += ["", "  Pulled models:"]

    for m in sorted(pulled, key=lambda x: x["size_gb"], reverse=True):
        band  = _fit_band(m["size_gb"], available)
        badge = {"safe": "✓", "tight": "⚠", "swap": "✗"}[band]
        lines.append(f"    {badge} {m['name']:<35} {m['size_gb']:>5.1f} GB  [{band}]")

    lines += ["", "  Role recommendations:", ""]

    recs = recommend()
    for role, info in recs.items():
        badge = {"safe": "✓", "tight": "⚠", "swap": "✗"}.get(info["band"], "?")
        lines.append(
            f"  {role:<20} → {badge} {info['model']:<35} {info['size_gb']:>5.1f} GB"
            f"  ({info['reason']})"
        )

    lines += [""]
    return "\n".join(lines)


def patch_registry(dry_run: bool = False) -> list[str]:
    """
    Update model_registry.yaml to use recommended models for each Ollama entry.
    Returns list of changes made (or would be made if dry_run=True).
    """
    recs = recommend()

    # Map registry roles to recommendation roles
    ROLE_MAP = {
        "code_review":    "code_review",
        "security_audit": "security_audit",
        "research":       "research",
        "assistant":      "assistant",
        "vision":         "vision",
    }

    with open(REGISTRY_PATH) as f:
        registry = yaml.safe_load(f)

    changes = []
    for model_id, meta in registry.get("models", {}).items():
        if meta.get("provider") != "ollama":
            continue
        role = meta.get("role", "")
        rec_role = ROLE_MAP.get(role)
        if not rec_role or rec_role not in recs:
            continue
        rec_model = recs[rec_role]["model"]
        current   = meta.get("model", "")
        if current != rec_model:
            changes.append(f"  {model_id}: {current} → {rec_model}")
            if not dry_run:
                meta["model"] = rec_model

    if not dry_run and changes:
        with open(REGISTRY_PATH, "w") as f:
            yaml.dump(registry, f, default_flow_style=False, sort_keys=False)

    return changes
