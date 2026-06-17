"""
Tests for memory/memory_manager.py and metrics/metrics_engine.py.
Uses a temp file for MemoryManager — no real disk state touched.
"""

import json
import os
import tempfile
import unittest

from memory.memory_manager import MemoryManager
from metrics.metrics_engine import MetricsEngine, _cost, CLOUD_RATES, LOCAL_MODEL_IDS


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_log(
    target_model: str = "ollama_qwen_coder",
    ollama_model: str = "qwen2.5-coder:14b",
    tokens_in: int = 200,
    tokens_out: int = 400,
    latency: float = 1.5,
    success: bool = True,
    fallback_used: bool = False,
    escalation_used: bool = False,
    intent: str = "Review.Code",
    confidence: float = 0.85,
) -> dict:
    return {
        "user_input":      "test prompt",
        "intent":          intent,
        "target_model":    target_model,
        "ollama_model":    ollama_model,
        "confidence":      confidence,
        "latency":         latency,
        "success":         success,
        "fallback_used":   fallback_used,
        "escalation_used": escalation_used,
        "tokens_in":       tokens_in,
        "tokens_out":      tokens_out,
        "notes":           "test",
    }


# ── MemoryManager ─────────────────────────────────────────────────────────────

class TestMemoryManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.mem = MemoryManager(storage_path=self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_starts_empty(self):
        self.assertEqual(self.mem.get_all_logs(), [])

    def test_log_task_persists(self):
        self.mem.log_task(_make_log())
        logs = self.mem.get_all_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["intent"], "Review.Code")

    def test_log_task_adds_timestamp(self):
        self.mem.log_task(_make_log())
        log = self.mem.get_all_logs()[0]
        self.assertIn("timestamp", log)
        self.assertIsInstance(log["timestamp"], str)

    def test_multiple_logs_appended(self):
        for i in range(5):
            self.mem.log_task(_make_log(intent=f"Intent.{i}"))
        self.assertEqual(len(self.mem.get_all_logs()), 5)

    def test_query_by_model_filters_correctly(self):
        self.mem.log_task(_make_log(target_model="ollama_qwen_coder"))
        self.mem.log_task(_make_log(target_model="claude_architect"))
        self.mem.log_task(_make_log(target_model="ollama_qwen_coder"))
        results = self.mem.query_by_model("ollama_qwen_coder")
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertEqual(r["target_model"], "ollama_qwen_coder")

    def test_query_by_model_empty_when_no_match(self):
        self.mem.log_task(_make_log(target_model="ollama_gemma"))
        self.assertEqual(self.mem.query_by_model("nonexistent_model"), [])

    def test_corrupted_file_returns_empty(self):
        with open(self.tmp.name, "w") as f:
            f.write("not valid json{{{")
        self.assertEqual(self.mem.get_all_logs(), [])

    def test_creates_file_if_missing(self):
        path = self.tmp.name + "_new.json"
        try:
            mem = MemoryManager(storage_path=path)
            self.assertTrue(os.path.exists(path))
            self.assertEqual(mem.get_all_logs(), [])
        finally:
            if os.path.exists(path):
                os.unlink(path)


# ── MetricsEngine ─────────────────────────────────────────────────────────────

class TestCostFunction(unittest.TestCase):
    def test_zero_tokens_is_zero_cost(self):
        self.assertEqual(_cost(0, 0, CLOUD_RATES["claude_architect"]), 0.0)

    def test_known_rate_calculation(self):
        # 1000 input tokens + 1000 output tokens at claude_architect rates
        cost = _cost(1000, 1000, CLOUD_RATES["claude_architect"])
        self.assertAlmostEqual(cost, 0.015 + 0.075, places=6)

    def test_codex_cheaper_than_claude(self):
        cost_claude = _cost(1000, 1000, CLOUD_RATES["claude_architect"])
        cost_codex  = _cost(1000, 1000, CLOUD_RATES["codex_primary"])
        self.assertLess(cost_codex, cost_claude)


class TestMetricsEngineEmpty(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.mem = MemoryManager(storage_path=self.tmp.name)
        self.engine = MetricsEngine(self.mem)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_get_metrics_empty_returns_status(self):
        result = self.engine.get_metrics()
        self.assertIn("status", result)

    def test_generate_report_empty_returns_string(self):
        result = self.engine.generate_report()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


class TestMetricsEngineWithData(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.mem = MemoryManager(storage_path=self.tmp.name)
        self.engine = MetricsEngine(self.mem)

        # 3 local runs
        for _ in range(3):
            self.mem.log_task(_make_log(
                target_model="ollama_qwen_coder",
                tokens_in=100, tokens_out=200, latency=2.0,
            ))
        # 1 cloud run
        self.mem.log_task(_make_log(
            target_model="claude_architect",
            ollama_model=None,
            tokens_in=500, tokens_out=800, latency=4.0,
        ))

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_total_tasks(self):
        m = self.engine.get_metrics()
        self.assertEqual(m["total_tasks"], 4)

    def test_local_vs_cloud_split(self):
        m = self.engine.get_metrics()
        self.assertEqual(m["local_tasks"], 3)
        self.assertEqual(m["cloud_tasks"], 1)

    def test_local_token_totals(self):
        m = self.engine.get_metrics()
        self.assertEqual(m["local_tokens_in"],  300)   # 3 × 100
        self.assertEqual(m["local_tokens_out"], 600)   # 3 × 200

    def test_cloud_cost_positive(self):
        m = self.engine.get_metrics()
        self.assertGreater(m["cloud_cost_usd"], 0.0)

    def test_savings_positive(self):
        m = self.engine.get_metrics()
        self.assertGreater(m["saved_vs_opus_usd"], 0.0)
        self.assertGreater(m["saved_vs_gpt4o_usd"], 0.0)

    def test_savings_opus_greater_than_gpt4o(self):
        # Claude Opus is more expensive than GPT-4o so savings vs Opus > savings vs GPT-4o
        m = self.engine.get_metrics()
        self.assertGreater(m["saved_vs_opus_usd"], m["saved_vs_gpt4o_usd"])

    def test_model_usage_counts(self):
        m = self.engine.get_metrics()
        self.assertEqual(m["model_usage"]["ollama_qwen_coder"], 3)
        self.assertEqual(m["model_usage"]["claude_architect"], 1)

    def test_success_rate_all_pass(self):
        m = self.engine.get_metrics()
        for model, rate in m["success_rate_per_model"].items():
            self.assertEqual(rate, 1.0)

    def test_fallback_frequency_zero(self):
        m = self.engine.get_metrics()
        self.assertEqual(m["fallback_frequency"], 0.0)

    def test_generate_report_contains_dashboard_header(self):
        report = self.engine.generate_report()
        self.assertIn("Token Savings Dashboard", report)

    def test_generate_report_contains_savings_lines(self):
        report = self.engine.generate_report()
        self.assertIn("vs Claude Opus", report)
        self.assertIn("vs GPT-4o", report)

    def test_generate_report_shows_local_model(self):
        report = self.engine.generate_report()
        self.assertIn("ollama_qwen_coder", report)

    def test_fallback_frequency_with_fallback(self):
        self.mem.log_task(_make_log(fallback_used=True))
        m = self.engine.get_metrics()
        self.assertGreater(m["fallback_frequency"], 0.0)

    def test_escalation_frequency_with_escalation(self):
        self.mem.log_task(_make_log(escalation_used=True))
        m = self.engine.get_metrics()
        self.assertGreater(m["escalation_frequency"], 0.0)


# ── Confidence function ───────────────────────────────────────────────────────

class TestCalculateConfidence(unittest.TestCase):
    def setUp(self):
        from routing.confidence import calculate_confidence
        self.calc = calculate_confidence

    def test_high_score_is_direct(self):
        self.assertEqual(self.calc(0.9)["decision"], "DIRECT")

    def test_exact_boundary_high_is_direct(self):
        self.assertEqual(self.calc(0.8)["decision"], "DIRECT")

    def test_mid_score_is_review(self):
        self.assertEqual(self.calc(0.65)["decision"], "REVIEW")

    def test_exact_boundary_mid_is_review(self):
        self.assertEqual(self.calc(0.5)["decision"], "REVIEW")

    def test_low_score_is_escalate(self):
        self.assertEqual(self.calc(0.3)["decision"], "ESCALATE")

    def test_zero_is_escalate(self):
        self.assertEqual(self.calc(0.0)["decision"], "ESCALATE")

    def test_one_is_direct(self):
        self.assertEqual(self.calc(1.0)["decision"], "DIRECT")

    def test_just_below_review_threshold_is_escalate(self):
        self.assertEqual(self.calc(0.499)["decision"], "ESCALATE")

    def test_just_below_direct_threshold_is_review(self):
        self.assertEqual(self.calc(0.799)["decision"], "REVIEW")

    def test_score_preserved_in_result(self):
        result = self.calc(0.73)
        self.assertAlmostEqual(result["score"], 0.73)

    def test_result_has_required_keys(self):
        result = self.calc(0.5)
        self.assertIn("score", result)
        self.assertIn("decision", result)


if __name__ == "__main__":
    unittest.main()
