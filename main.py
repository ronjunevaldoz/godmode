import sys
import time
import yaml
from typing import Tuple

from routing.router import route_request
from routing.provider_adapter import ProviderAdapter
from routing.model_selector import ModelSelector
from memory.memory_manager import MemoryManager
from metrics.metrics_engine import MetricsEngine

memory  = MemoryManager()
metrics = MetricsEngine(memory)
adapter = ProviderAdapter()
selector = ModelSelector()

with open("configs/fallback_chain.yaml") as f:
    FALLBACK_CONFIG = yaml.safe_load(f)


def run_with_retry(model_id: str, prompt: str, context: dict | None = None) -> Tuple[str, bool, bool]:
    policy = selector.get_fallback_chain(model_id)
    retries = 0 if model_id.startswith("ollama") else 1
    fallback_used = False

    for attempt in range(retries + 1):
        try:
            result = adapter.execute(model_id, prompt, context)
            return result, True, fallback_used
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed for {model_id}: {e}")

    for fallback in policy:
        print(f"  Falling back to {fallback}...")
        fallback_used = True
        try:
            result = adapter.execute(fallback, prompt, context)
            return result, True, fallback_used
        except Exception as e:
            print(f"  Fallback {fallback} also failed: {e}")

    return "All attempts and fallbacks failed.", False, fallback_used


def orchestrate(user_input: str) -> None:
    print(f"\n{'─' * 60}")
    start = time.time()

    routing = route_request(user_input)
    intent   = routing["intent"]
    decision = routing["decision"]
    model_id = routing["model_id"]

    print(f"  Intent    : {intent}")
    print(f"  Model     : {model_id}  [{decision}]  confidence={routing['confidence']:.2f}")

    escalation_used = (
        model_id == "claude_architect"
        and "Architecture" not in intent
        and "Review.Architecture" != intent
    )

    result, success, fallback_used = run_with_retry(model_id, user_input)

    if decision == "REVIEW" and success:
        print("  L3 Governor: reviewing specialist output...")
        _, result = adapter.validate_result(model_id, user_input, result)

    latency = time.time() - start

    # Token counts (populated by OllamaUtilityAgent after execute)
    tokens_in, tokens_out = adapter.get_token_counts(model_id)

    # Estimate for cloud agents (no direct count available)
    if not tokens_in:
        tokens_in  = len(user_input) // 4
        tokens_out = len(result) // 4

    memory.log_task({
        "user_input":      user_input,
        "intent":          intent,
        "target_model":    model_id,
        "ollama_model":    getattr(adapter._agents.get(model_id), "model", None),
        "confidence":      routing["confidence"],
        "latency":         latency,
        "success":         success,
        "fallback_used":   fallback_used,
        "escalation_used": escalation_used,
        "tokens_in":       tokens_in,
        "tokens_out":      tokens_out,
        "notes":           f"Decision: {decision}",
    })

    print(f"\n{result}")
    print(f"\n  ✓ {latency:.1f}s  |  tokens in={tokens_in} out={tokens_out}  |  "
          f"fallback={fallback_used}")
    print(f"{'─' * 60}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        orchestrate(" ".join(sys.argv[1:]))
    else:
        print("Usage: python3 main.py 'your prompt'")
