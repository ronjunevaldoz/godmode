import sys
import time
import yaml
from typing import Dict, Any, Tuple

from routing.router import route_request
from routing.provider_adapter import ProviderAdapter
from routing.model_selector import ModelSelector
from memory.memory_manager import MemoryManager
from metrics.metrics_engine import MetricsEngine

# Initialize Components
memory = MemoryManager()
metrics = MetricsEngine(memory)
adapter = ProviderAdapter()
selector = ModelSelector()

# Load Retry/Fallback Config
with open("configs/fallback_chain.yaml", "r") as f:
    FALLBACK_CONFIG = yaml.safe_load(f)

def run_with_retry(model_id: str, prompt: str, context: dict = None) -> Tuple[str, bool, bool]:
    """
    Executes a task using the ProviderAdapter, applying retry and fallback logic.
    """
    # We look at the registry for fallbacks now, not the separate config
    policy = selector.get_fallback_chain(model_id)

    # For simplicity in this version, we use a fixed retry count of 1 for all cloud models
    # In a full production system, this would be in the registry.yaml
    retries = 1 if model_id != "ollama_qwen" else 0

    current_model = model_id
    fallback_used = False

    # 1. Primary Model Attempt
    for attempt in range(retries + 1):
        try:
            result = adapter.execute(current_model, prompt, context)
            return result, True, fallback_used
        except Exception as e:
            print(f"Attempt {attempt+1} failed for {current_model}: {e}")

    # 2. Fallback Chain Attempt
    for fallback_model in policy:
        print(f"Falling back to {fallback_model}...")
        fallback_used = True
        try:
            result = adapter.execute(fallback_model, prompt, context)
            return result, True, fallback_used
        except Exception as e:
            print(f"Fallback {fallback_model} also failed: {e}")

    return "All attempts and fallbacks failed.", False, fallback_used

def orchestrate(user_input: str):
    print(f"\n--- New Request ---")
    start_time = time.time()

    # Step 1: L1 Triage & Model Selection
    routing_data = route_request(user_input)
    intent = routing_data["intent"]
    decision = routing_data["decision"]
    model_id = routing_data["model_id"]

    print(f"L1 Router -> Intent: {intent} | Confidence: {routing_data['confidence']} | Decision: {decision} | ModelID: {model_id}")

    # Step 2: Execution with Retry/Fallback via Adapter
    escalation_used = (model_id == "claude_architect" and "Architecture" not in intent and "Review" not in intent)

    result, success, fallback_used = run_with_retry(model_id, user_input)

    # Step 3: Optional L3 Validation
    if decision == 'REVIEW' and success:
        print(f"L3 Governor: Reviewing Specialist output...")
        is_valid, final_result = adapter.validate_result(model_id, user_input, result)
        if not is_valid:
            result = final_result
            escalation_used = True

    latency = time.time() - start_time

    # Step 4: Log to Memory
    memory.log_task({
        "user_input": user_input,
        "intent": intent,
        "target_model": model_id,
        "confidence": routing_data["confidence"],
        "latency": latency,
        "success": success,
        "fallback_used": fallback_used,
        "escalation_used": escalation_used,
        "notes": f"Decision: {decision}"
    })

    print(f"Final Output: {result}")
    print(f"Stats: {latency:.3f}s | Success: {success} | Fallback: {fallback_used}")
    print(f"-------------------\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
        orchestrate(user_query)
    else:
        print("Please provide a query: python3 main.py 'Your request here'")
