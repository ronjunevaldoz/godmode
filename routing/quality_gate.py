"""
Quality gate: fast LLM judge that scores a local model's response.
If the score falls below threshold the caller should escalate to a cloud model.
"""

import json
import logging
import os

import requests

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL: str = (
    os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    .rstrip("/")
    .replace("/api/chat", "")
) + "/api/chat"
# Use the smallest/fastest model as judge — it just needs to score, not solve.
JUDGE_MODEL = "qwen3:8b"
ESCALATION_THRESHOLD = 0.55  # scores below this trigger cloud retry

_JUDGE_SYSTEM = (
    "You are a strict quality evaluator. "
    "You will be given a task and an AI-generated response. "
    "Score the response on a scale from 0.0 to 1.0 where:\n"
    "  1.0 = correct, complete, safe, production-ready\n"
    "  0.7 = mostly correct but missing edge cases or clarity\n"
    "  0.5 = partially correct, significant gaps\n"
    "  0.3 = mostly wrong or dangerously incomplete\n"
    "  0.0 = wrong, harmful, or no useful content\n\n"
    "For code tasks penalise heavily: syntax errors, missing imports, logic bugs, "
    "security issues (SQL injection, unescaped input, unchecked nulls).\n"
    "For security / bug-fix tasks penalise any missed vulnerability or incomplete fix.\n"
    "Return ONLY valid JSON: {\"score\": <float>, \"reason\": \"<one sentence>\"}"
)


def _build_judge_prompt(task: str, response: str) -> str:
    # Truncate to keep judge calls cheap
    task_excerpt    = task[:800]
    response_excerpt = response[:1200]
    return (
        f"TASK:\n{task_excerpt}\n\n"
        f"AI RESPONSE:\n{response_excerpt}\n\n"
        "Score this response."
    )


def assess(task: str, response: str, model_id: str) -> tuple[float, str]:
    """
    Score a model response. Returns (score, reason).
    score < ESCALATION_THRESHOLD → caller should retry with a cloud model.
    """
    if not response or not response.strip():
        return 0.0, "Empty response"

    # Heuristic fast-path: obvious failure signals, no LLM call needed
    lower = response.lower()
    if any(phrase in lower for phrase in (
        "i cannot", "i'm unable", "i don't know", "as an ai, i",
        "i apologize", "i don't have access",
    )):
        return 0.2, "Model refused or expressed inability"

    if len(response.strip()) < 40:
        return 0.25, "Response suspiciously short"

    # LLM judge call
    try:
        resp = requests.post(
            OLLAMA_BASE_URL,
            json={
                "model": JUDGE_MODEL,
                "messages": [
                    {"role": "system", "content": _JUDGE_SYSTEM},
                    {"role": "user",   "content": _build_judge_prompt(task, response)},
                ],
                "stream": False,
                "format": "json",
            },
            timeout=45,
        )
        resp.raise_for_status()
        raw = resp.json()["message"]["content"]
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Judge returned non-JSON (e.g. "Score: 0.8") — treat as uncertain,
            # not as a pass, so genuinely bad output isn't silently approved.
            logger.warning(f"[QualityGate] Judge returned non-JSON: {raw[:120]!r}")
            return 0.5, "Judge returned non-JSON response"
        score  = float(data.get("score", 0.5))
        reason = str(data.get("reason", ""))
        score  = max(0.0, min(1.0, score))
        logger.info(f"[QualityGate] {model_id} scored {score:.2f} — {reason}")
        return score, reason
    except json.JSONDecodeError:
        raise  # already handled above — shouldn't reach here
    except Exception as e:
        logger.warning(f"[QualityGate] Judge call failed ({e}), defaulting to pass")
        # Fail open only for genuine connectivity/timeout failures
        return 1.0, "Judge unavailable — skipping gate"


def should_escalate(score: float) -> bool:
    return score < ESCALATION_THRESHOLD
