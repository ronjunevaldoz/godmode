import sys
import time
import yaml
from typing import Dict, Any, Tuple

from routing.router import route_request
from agents.ollama_utility import OllamaUtilityAgent
from agents.codex_engineer import CodexEngineerAgent
from agents.gemini_vision import GeminiVisionAgent
from agents.claude_architect import ClaudeArchitectAgent

from memory.memory_manager import MemoryManager
from metrics.metrics_engine import MetricsEngine

# Initialize Memory and Metrics
memory = MemoryManager()
metrics = MetricsEngine(memory)

# Load Retry/Fallback Config
with open("configs/fallback_chain.yaml", "r") as f:
    FALLBACK_CONFIG = yaml.safe_load(f)

# Initialize Agents
AGENTS = {
    "ollama": OllamaUtilityAgent(),
    "codex": CodexEngineerAgent(),
    "gemini": GeminiVisionAgent(),
    "claude": ClaudeArchitectAgent()
}

def run_with_retry(model_name: str, prompt: str, context: dict = None) -> Tuple[str, bool, bool]:
    """
    Executes a task with the specified model, applying retry and fallback logic.
    Returns: (result, success, fallback_used)
    """
    policy = FALLBACK_CONFIG["retry_policies"].get(model_name, {"retries": 0, "fallback": []})
    retries = policy.get("retries", 0)
    fallbacks = policy.get("fallback", [])

    current_model = model_name
    fallback_used = False

    # 1. Primary Model Attempt (with retries)
    for attempt in range(retries + 1):
        try:
            agent = AGENTS.get(current_model)
            if not agent:
                raise ValueError(f"Agent {current_model} not configured")

            result = agent.execute(prompt, context)
            # In a real system, we'd verify if the result is actually successful
            # For now, if it didn't crash, it's a success.
            return result, True, fallback_used
        except Exception as e:
            print(f"Attempt {attempt+1} failed for {current_model}: {e}")

    # 2. Fallback Chain Attempt
    for fallback_model in fallbacks:
        print(f"Falling back to {fallback_model}...")
        fallback_used = True
        try:
            agent = AGENTS.get(fallback_model)
            if agent:
                result = agent.execute(prompt, context)
                return result, True, fallback_used
        except Exception as e:
            print(f"Fallback {fallback_model} also failed: {e}")

    return "All attempts and fallbacks failed.", False, fallback_used

def orchestrate(user_input: str):
    print(f"\n--- New Request ---")
    start_time = time.time()

    # Step 1: L1 Triage
    routing_data = route_request(user_input)
    intent = routing_data["intent"]
    decision = routing_data["decision"]
    target_model = routing_data["target_model"]

    print(f"L1 Router -> Intent: {intent} | Confidence: {routing_data['confidence']} | Decision: {decision} | Target: {target_model}")

    # Step 2: Execution with Retry/Fallback
    escalation_used = (target_model == "claude" and "Architecture" not in intent and "Review" not in intent)

    result, success, fallback_used = run_with_retry(target_model, user_input)

    # Step 3: Optional L3 Validation (if Decision was 'REVIEW')
    if decision == 'REVIEW' and success:
        print(f"L3 Governor: Reviewing Specialist output...")
        is_valid, final_result = AGENTS["claude"].validate_result(user_input, result)
        if not is_valid:
            result = final_result
            escalation_used = True

    latency = time.time() - start_time

    # Step 4: Log to Memory
    memory.log_task({
        "user_input": user_input,
        "intent": intent,
        "target_model": target_model,
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
