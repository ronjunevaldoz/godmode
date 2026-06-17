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

    # Hard governance routes (only architecture and top-level review need Claude)
    if conf_result["decision"] == "ESCALATE":
        model_id = "claude_architect"

    if intent in {"Architecture.System", "Architecture.Mobile", "Architecture.Agent",
                  "Review.Architecture", "Documentation.Spec"}:
        model_id = "claude_architect"

    return {
        "intent": intent,
        "confidence": score,
        "decision": conf_result["decision"],
        "model_id": model_id,
        "required_capabilities": required_capabilities,
    }
