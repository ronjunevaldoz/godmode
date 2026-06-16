import json
import requests
from typing import Dict, Any, Tuple
from .confidence import calculate_confidence
from .capabilities import find_best_model

# Configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3"

# Updated Granular Intent Hierarchy
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

def load_intent_map() -> Dict[str, list]:
    with open("routing/intent_map.json", "r") as f:
        return json.load(f)

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
        print(f"Routing error: {e}")
        return "UNKNOWN", 0.0

def route_request(user_input: str) -> Dict[str, Any]:
    """
    Enhanced Routing: Intent -> Capabilities -> Best Model.
    """
    intent, score = classify_intent(user_input)
    conf_result = calculate_confidence(score)
    intent_map = load_intent_map()

    # Get required capabilities for the detected intent
    required_capabilities = intent_map.get(intent, intent_map["UNKNOWN"])

    # Find best model based on capabilities
    target_model = find_best_model(required_capabilities)

    # Overrides for high-level governance or low confidence
    if conf_result["decision"] == 'ESCALATE':
        target_model = "claude"

    # Hard-route strategy/validation to Claude regardless of capabilities if required by policy
    if "Architecture" in intent or "Review" in intent:
        target_model = "claude"

    return {
        "intent": intent,
        "confidence": score,
        "decision": conf_result["decision"],
        "target_model": target_model,
        "required_capabilities": required_capabilities
    }
