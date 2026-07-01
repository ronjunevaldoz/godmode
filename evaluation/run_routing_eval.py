import json
from pathlib import Path

from routing.router import route_request

ROOT = Path(__file__).resolve().parent.parent

def run_eval():
    with open(ROOT / "evaluation" / "routing_cases.json", "r") as f:
        cases = json.load(f)

    print(f"{'Prompt':<50} | {'Expected Intent':<25} | {'Actual Intent':<25} | {'Result'}")
    print("-" * 110)

    passed = 0
    for case in cases:
        prompt = case["prompt"]
        expected_intent = case["expected_intent"]
        expected_model = case["expected_model_id"]

        result = route_request(prompt)
        actual_intent = result["intent"]
        actual_model = result["model_id"]

        is_correct = (actual_intent == expected_intent) and (actual_model == expected_model)
        if is_correct:
            passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        print(f"{prompt[:48]:<50} | {expected_intent:<25} | {actual_intent:<25} | {status}")
        if not is_correct:
            print(f"   Expected: {expected_model}, Got: {actual_model}")

    print("-" * 110)
    print(f"Final Score: {passed}/{len(cases)} ({passed/len(cases):.2%})")

if __name__ == "__main__":
    run_eval()
