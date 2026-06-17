import json
import logging
import os
import requests
from typing import Dict, Any, Tuple
from .confidence import calculate_confidence
from .capability_resolver import CapabilityResolver
from .model_selector import ModelSelector

logger = logging.getLogger(__name__)

# Configuration from environment variables
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "https://ron-local-home.duckdns.org/ollama/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Granular Intent Hierarchy
INTENT_CATEGORIES = [
    "Implementation.Android", "Implementation.KMP", "Implementation.JNI",
    "Implementation.Backend", "Implementation.DevOps", "Implementation.Web",
    "Architecture.System", "Architecture.Mobile", "Architecture.Agent",
    "Multimodal.UI", "Multimodal.Image",
    "Utility.Summary", "Utility.Classification", "Utility.Extraction",
    "Documentation.Spec", "Documentation.Markdown",
    "Review.Code", "Review.Architecture",
    "UNKNOWN"
]

# Initialize components
resolver = CapabilityResolver()
selector = ModelSelector()

def classify_intent(user_input: str) -> Tuple[str, float]:
    """
    Uses Ollama to classify the intent into the granular hierarchy.
    """
    prompt = (
        f"Classify the following user request into exactly one of these categories: {', '.join(INTENT_CATEGORIES)}.\n"
        f"Return your answer in JSON format with two keys: 'intent' (the category) and 'confidence' (a float between 0.0 and 1.0).\n\n"
        f"Request: {user_input}\n"
        f"JSON response:"
    )

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json"
            }
        )
        response.raise_for_status()
        result = response.json()['message']['content']
        data = json.loads(result)

        intent = data.get("intent", "UNKNOWN")
        if intent not in INTENT_CATEGORIES:
            intent = "UNKNOWN"

        return intent, data.get("confidence", 0.0)
    except Exception as e:
        logger.error(f"Routing error: {e}")
        return "UNKNOWN", 0.0

def route_request(user_input: str) -> Dict[str, Any]:
    """
    Refactored Routing: Intent -> Capabilities -> Model Registry -> Model ID.
    """
    # 1. Triage Intent
    intent, score = classify_intent(user_input)
    conf_result = calculate_confidence(score)

    # 2. Resolve Capabilities
    required_capabilities = resolver.resolve_capabilities(intent)

    # 3. Determine Selection Options (Local-First/Multimodal flags)
    options = {
        "privacy": "cloud", # Default
        "multimodal": False
    }

    # Local-first heuristic
    if "Utility" in intent or "Classification" in intent:
        options["privacy"] = "local"

    # Multimodal heuristic
    if "Multimodal" in intent or "UI" in intent or "Image" in intent:
        options["multimodal"] = True

    # 4. Select Best Model from Registry
    model_id = selector.select_best_model(required_capabilities, options)

    # 5. High-level Governance Overrides
    # If confidence is too low, we escalate to the high-reasoning model
    if conf_result["decision"] == 'ESCALATE':
        model_id = "claude_architect"

    # Hard-route architecture and review to Claude for safety
    if "Architecture" in intent or "Review" in intent:
        model_id = "claude_architect"

    return {
        "intent": intent,
        "confidence": score,
        "decision": conf_result["decision"],
        "model_id": model_id,
        "required_capabilities": required_capabilities
    }