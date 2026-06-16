from typing import List, Dict

# Capability Matrix: Which models provide which capabilities?
CAPABILITY_MATRIX = {
    "codex": {
        "capabilities": [
            "code_execution",
            "repo_awareness",
            "documentation_generation"
        ],
        "cost": "medium",
        "privacy": "cloud"
    },
    "gemini": {
        "capabilities": [
            "multimodal_understanding",
            "cheap_batch_processing"
        ],
        "cost": "medium",
        "privacy": "cloud"
    },
    "ollama": {
        "capabilities": [
            "private_local_processing",
            "cheap_batch_processing"
        ],
        "cost": "low",
        "privacy": "local"
    },
    "claude": {
        "capabilities": [
            "long_context_reasoning",
            "architecture_review",
            "final_validation",
            "documentation_generation"
        ],
        "cost": "high",
        "privacy": "cloud"
    }
}

def find_best_model(required_capabilities: List[str]) -> str:
    """
    Selects the best model based on required capabilities,
    preferring the cheapest model that satisfies all requirements.
    """
    candidates = []

    for model, data in CAPABILITY_MATRIX.items():
        # Check if all required capabilities are present in the model
        if all(cap in data["capabilities"] for cap in required_capabilities):
            candidates.append(model)

    if not candidates:
        # Fallback to Claude if no perfect match is found, as it's the most capable
        return "claude"

    # Sort candidates by cost: low -> medium -> high
    cost_priority = {"low": 0, "medium": 1, "high": 2}
    candidates.sort(key=lambda m: cost_priority[CAPABILITY_MATRIX[m]["cost"]])

    return candidates[0]
