from typing import TypedDict, Optional

class ConfidenceResult(TypedDict):
    score: float
    decision: str  # 'DIRECT', 'REVIEW', 'ESCALATE'

def calculate_confidence(model_score: float) -> ConfidenceResult:
    """
    Determines the routing decision based on the L1 router's confidence score.

    Args:
        model_score (float): The confidence score provided by the router (0.0 to 1.0).

    Returns:
        ConfidenceResult: A dictionary containing the score and the routing decision.
    """
    if model_score >= 0.8:
        decision = 'DIRECT'
    elif 0.5 <= model_score < 0.8:
        decision = 'REVIEW'
    else:
        decision = 'ESCALATE'

    return {
        "score": model_score,
        "decision": decision
    }
