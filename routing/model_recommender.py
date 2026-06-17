"""
System-aware Ollama model recommender.

Reads available RAM, queries Ollama for pulled models, scores each model
per role, and returns the best fit. Can optionally patch model_registry.yaml.
"""

import logging
import os
import platform
import subprocess
import yaml
import requests

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL: str = os.getenv(
    "OLLAMA_BASE_URL", "https://ron-local-home.duckdns.org/ollama"
).replace("/api/chat", "")

REGISTRY_PATH = "configs/model_registry.yaml"

# How much RAM (GB) to reserve for the OS + other processes
OS_OVERHEAD_GB = 3.5

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
    "research":       ["gemma", "llama", "qwen", "hermes"],
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


def _get_ram_gb() -> float:
    """Return total system RAM in GB."""
    try:
        if platform.system() == "Darwin":
            result = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)
            return int(result.strip()) / 1e9
        # Linux
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal"):
                    return int(line.split()[1]) / 1e6
    except Exception as e:
        logger.warning(f"Could not read RAM: {e}")
    return 16.0  # safe default


def _is_apple_silicon() -> bool:
    try:
        result = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True)
        return "Apple" in result
    except Exception:
        return False


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
    ram_gb = _get_ram_gb()
    unified = _is_apple_silicon()
    available_gb = ram_gb - OS_OVERHEAD_GB

    pulled = _get_pulled_models()
    if not pulled:
        return {}

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
    ram_gb     = _get_ram_gb()
    unified    = _is_apple_silicon()
    available  = ram_gb - OS_OVERHEAD_GB
    pulled     = _get_pulled_models()

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════╗",
        "║          Godmode Model Recommendation Report             ║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
        f"  System : {'Apple Silicon (unified memory)' if unified else platform.processor()}",
        f"  RAM    : {ram_gb:.0f} GB total  →  {available:.1f} GB available for models",
        "",
        "  Pulled models:",
    ]

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
