import json
import logging
import os
import requests
from .confidence import calculate_confidence
from .capability_resolver import CapabilityResolver
from .model_selector import ModelSelector

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "https://ron-local-home.duckdns.org/ollama/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

# Intents where a wrong answer causes real harm — always use cloud
HIGH_STAKES_INTENTS: frozenset[str] = frozenset({
    "Fix.Bug",
    "Review.Security",
})

# Keywords that signal dangerous or highly complex work within any intent
_DANGER_KEYWORDS: frozenset[str] = frozenset({
    "auth", "authentication", "authorization", "oauth", "jwt",
    "payment", "billing", "stripe", "wallet",
    "crypto", "encrypt", "decrypt", "hash", "salt",
    "sql", "injection", "xss", "csrf", "overflow",
    "race condition", "concurrency", "deadlock", "mutex",
    "permission", "privilege", "rbac", "acl",
    "production", "prod", "live", "release",
    "vulnerability", "exploit", "cve",
})

_COMPLEXITY_LENGTH = 600  # chars — above this, prompt is "complex"


def _complexity(prompt: str) -> str:
    """Returns 'high', 'medium', or 'low' based on length + keyword signals."""
    lower = prompt.lower()
    hits = sum(1 for kw in _DANGER_KEYWORDS if kw in lower)
    if hits >= 2 or len(prompt) > 1200:
        return "high"
    if hits >= 1 or len(prompt) > _COMPLEXITY_LENGTH:
        return "medium"
    return "low"


INTENT_CATEGORIES = [
    "Implementation.Android", "Implementation.KMP", "Implementation.JNI",
    "Implementation.Backend", "Implementation.DevOps", "Implementation.Web",
    "Architecture.System", "Architecture.Mobile", "Architecture.Agent",
    "Review.Code", "Review.Security", "Review.Architecture",
    "Test.Unit",
    "Fix.Bug",
    "Improve.Code", "Improve.Prompt",
    "Multimodal.UI", "Multimodal.Image",
    "Utility.Summary", "Utility.Classification", "Utility.Extraction",
    "Documentation.Spec", "Documentation.Markdown",
    "Research.General",
    "Assistant.General",
    "UNKNOWN",
]

resolver = CapabilityResolver()
selector = ModelSelector()


def classify_intent(user_input: str) -> tuple[str, float]:
    prompt = (
        f"Classify the following user request into exactly one of these categories: "
        f"{', '.join(INTENT_CATEGORIES)}.\n"
        f"Return your answer in JSON format with two keys: 'intent' (the category) "
        f"and 'confidence' (a float between 0.0 and 1.0).\n\n"
        f"Request: {user_input}\nJSON response:"
    )
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
            },
            timeout=30,
        )
        response.raise_for_status()
        data = json.loads(response.json()["message"]["content"])
        intent = data.get("intent", "UNKNOWN")
        if intent not in INTENT_CATEGORIES:
            intent = "UNKNOWN"
        return intent, data.get("confidence", 0.0)
    except Exception as e:
        logger.error(f"Routing error: {e}")
        return "UNKNOWN", 0.0


def route_request(user_input: str) -> dict:
    intent, score = classify_intent(user_input)
    conf_result = calculate_confidence(score)
    required_capabilities = resolver.resolve_capabilities(intent)

    options: dict = {"privacy": "cloud", "multimodal": False}

    # Local-first: utility, classification, fast tasks
    if any(k in intent for k in ("Utility", "Classification", "Assistant", "Research")):
        options["privacy"] = "local"

    # Multimodal
    if any(k in intent for k in ("Multimodal", "UI", "Image")):
        options["multimodal"] = True

    model_id = selector.select_best_model(required_capabilities, options)
    complexity = _complexity(user_input)
    escalation_reason: str | None = None

    # ── Tier 1: hard governance — always cloud ──────────────────────────────
    if intent in {"Architecture.System", "Architecture.Mobile", "Architecture.Agent",
                  "Review.Architecture", "Documentation.Spec"}:
        model_id = "claude_architect"
        escalation_reason = "architecture/spec governance"

    # ── Tier 2: high-stakes intents — cloud by default ──────────────────────
    elif intent in HIGH_STAKES_INTENTS:
        model_id = "codex_primary"
        escalation_reason = f"high-stakes intent ({intent})"

    # ── Tier 3: complexity escalation — dangerous keywords or very long prompt
    elif complexity == "high" and model_id not in ("claude_architect", "codex_primary"):
        model_id = "codex_primary"
        escalation_reason = "complexity gate (danger keywords or long prompt)"

    # ── Tier 4: low-confidence catch-all ────────────────────────────────────
    elif conf_result["decision"] == "ESCALATE":
        model_id = "claude_architect"
        escalation_reason = "low routing confidence"

    if escalation_reason:
        logger.info(f"[Router] Escalated to {model_id}: {escalation_reason}")

    return {
        "intent": intent,
        "confidence": score,
        "decision": conf_result["decision"],
        "model_id": model_id,
        "complexity": complexity,
        "escalation_reason": escalation_reason,
        "required_capabilities": required_capabilities,
    }
