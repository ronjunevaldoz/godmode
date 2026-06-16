import json
from typing import Dict, Any, List
from memory.memory_manager import MemoryManager

class MetricsEngine:
    """
    Aggregates routing telemetry from execution memory.
    """
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager

    def get_metrics(self) -> Dict[str, Any]:
        logs = self.memory.get_all_logs()
        if not logs:
            return {"status": "No data available"}

        total_tasks = len(logs)
        model_counts = {}
        fallback_count = 0
        escalation_count = 0
        intent_confidence = {} # intent -> list of scores
        model_success = {} # model -> [successes, totals]

        for log in logs:
            # Usage counts
            model = log.get("target_model", "unknown")
            model_counts[model] = model_counts.get(model, 0) + 1

            # Fallbacks/Escalations
            if log.get("fallback_used"):
                fallback_count += 1
            if log.get("escalation_used"):
                escalation_count += 1

            # Confidence per intent
            intent = log.get("intent", "unknown")
            score = log.get("confidence", 0.0)
            if intent not in intent_confidence:
                intent_confidence[intent] = []
            intent_confidence[intent].append(score)

            # Success rates
            success = log.get("success", False)
            if model not in model_success:
                model_success[model] = [0, 0]
            model_success[model][1] += 1
            if success:
                model_success[model][0] += 1

        # Calculate Averages
        avg_confidence = {
            intent: (sum(scores) / len(scores))
            for intent, scores in intent_confidence.items()
        }

        success_rates = {
            model: (s[0]/s[1]) if s[1] > 0 else 0
            for model, s in model_success.items()
        }

        return {
            "total_tasks": total_tasks,
            "model_usage": model_counts,
            "fallback_frequency": fallback_count / total_tasks,
            "escalation_frequency": escalation_count / total_tasks,
            "average_confidence_per_intent": avg_confidence,
            "success_rate_per_model": success_rates
        }

    def generate_report(self) -> str:
        metrics = self.get_metrics()
        if "status" in metrics: return metrics["status"]

        report = [
            "=== Agent Routing Metrics Report ===",
            f"Total Tasks: {metrics['total_tasks']}",
            f"Fallback Rate: {metrics['fallback_frequency']:.2%}",
            f"Escalation Rate: {metrics['escalation_frequency']:.2%}",
            "\nModel Usage:",
        ]
        for model, count in metrics['model_usage'].items():
            report.append(f" - {model}: {count}")

        report.append("\nSuccess Rates:")
        for model, rate in metrics['success_rate_per_model'].items():
            report.append(f" - {model}: {rate:.2%}")

        report.append("\nAvg Confidence per Intent:")
        for intent, score in metrics['average_confidence_per_intent'].items():
            report.append(f" - {intent}: {score:.2f}")

        return "\n".join(report)
