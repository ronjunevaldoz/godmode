"""
Integration tests for main.orchestrate().

Requires:
  - Ollama server reachable (OLLAMA_BASE_URL)
  - No cloud API keys needed (GODMODE_MODE=skill is default)

Run selectively:
  pytest tests/test_integration.py -v -m integration
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ollama_reachable() -> bool:
    try:
        import requests
        base = os.getenv("OLLAMA_BASE_URL",
                         "http://localhost:11434").replace("/api/chat", "")
        resp = requests.get(f"{base}/api/tags", timeout=5)
        return resp.ok
    except Exception:
        return False


OLLAMA_UP = _ollama_reachable()
requires_ollama = pytest.mark.skipif(
    not OLLAMA_UP,
    reason="Ollama server not reachable — set OLLAMA_BASE_URL or start the server",
)


# ── orchestrate() with fully mocked adapter ───────────────────────────────────

class TestOrchestrateUnit(unittest.TestCase):
    """
    Unit-level orchestrate tests: router and adapter both mocked.
    Verifies orchestrate() contract without any network calls.
    """

    def _run(self, prompt: str, intent: str, model_id: str,
             mock_result: str = "Mock result from local model.",
             review_required: bool = False) -> dict:
        """Patch classify_intent + adapter.execute, call orchestrate(), return last memory log."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name
        try:
            routing_return = {
                "intent":               intent,
                "confidence":           0.88,
                "decision":             "DIRECT",
                "model_id":             model_id,
                "complexity":           "low",
                "escalation_reason":    None,
                "review_required":      review_required,
                "required_capabilities": [],
            }
            with (
                patch("routing.router.classify_intent", return_value=(intent, 0.88)),
                patch("routing.provider_adapter.ProviderAdapter.execute", return_value=mock_result),
                patch("routing.quality_gate.requests.post",
                      side_effect=ConnectionError("judge offline")),
                patch("memory.memory_manager.MemoryManager.storage_path", tmp_path, create=True),
            ):
                # Reload main so module-level globals use the patched tmp path
                import importlib
                import main as m
                # Directly write log to temp path to verify contract
                from memory.memory_manager import MemoryManager
                mem = MemoryManager(storage_path=tmp_path)

                # Manually invoke with fresh memory
                with patch.object(m, "memory", mem):
                    m.orchestrate(prompt)

                return mem.get_all_logs()[-1]
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_log_entry_has_required_keys(self):
        log = self._run("summarize logs", "Utility.Summary", "ollama_gemma")
        for key in ("user_input", "intent", "target_model", "confidence",
                    "latency", "success", "tokens_in", "tokens_out"):
            self.assertIn(key, log, f"Missing key: {key}")

    def test_log_records_correct_intent(self):
        log = self._run("summarize logs", "Utility.Summary", "ollama_gemma")
        self.assertEqual(log["intent"], "Utility.Summary")

    def test_log_records_success_true(self):
        log = self._run("summarize logs", "Utility.Summary", "ollama_gemma")
        self.assertTrue(log["success"])

    def test_log_token_estimates_positive(self):
        log = self._run("summarize this long log", "Utility.Summary", "ollama_gemma",
                        mock_result="Here is the summary of the log entries.")
        self.assertGreater(log["tokens_in"], 0)
        self.assertGreater(log["tokens_out"], 0)

    def test_review_required_flag_logged(self):
        log = self._run("fix the bug", "Fix.Bug", "ollama_qwen_coder",
                        review_required=True)
        self.assertTrue(log.get("review_required"))

    def test_review_result_contains_header(self, ):
        """When review_required=True the printed result should contain the NEEDS REVIEW block."""
        import io
        from contextlib import redirect_stdout

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name
        try:
            from memory.memory_manager import MemoryManager
            mem = MemoryManager(storage_path=tmp_path)
            import main as m
            buf = io.StringIO()
            with (
                patch("routing.router.classify_intent", return_value=("Fix.Bug", 0.88)),
                patch("routing.provider_adapter.ProviderAdapter.execute",
                      return_value="Use null check before dereference."),
                patch("routing.quality_gate.requests.post",
                      side_effect=ConnectionError),
                patch.object(m, "memory", mem),
                redirect_stdout(buf),
            ):
                m.orchestrate("fix the null pointer exception")
            output = buf.getvalue()
            self.assertIn("NEEDS REVIEW", output)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


# ── Live integration (Ollama must be up) ─────────────────────────────────────

@pytest.mark.integration
class TestOrchestrateIntegration(unittest.TestCase):
    """
    Full round-trip: real Ollama triage + real local model execution.
    Skipped automatically when Ollama is not reachable.
    """

    @requires_ollama
    def test_utility_prompt_completes(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name
        try:
            from memory.memory_manager import MemoryManager
            mem = MemoryManager(storage_path=tmp_path)
            import main as m
            with patch.object(m, "memory", mem):
                m.orchestrate("Summarise in one sentence: the sky is blue.")
            logs = mem.get_all_logs()
            self.assertEqual(len(logs), 1)
            self.assertTrue(logs[0]["success"])
            self.assertIn("ollama", logs[0]["target_model"])
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @requires_ollama
    def test_fix_bug_flagged_for_review_in_skill_mode(self):
        from routing.router import SKILL_MODE
        if not SKILL_MODE:
            self.skipTest("Only relevant in skill mode")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name
        try:
            from memory.memory_manager import MemoryManager
            mem = MemoryManager(storage_path=tmp_path)
            import main as m
            with patch.object(m, "memory", mem):
                m.orchestrate("Fix the null pointer bug in the payment handler.")
            log = mem.get_all_logs()[-1]
            self.assertTrue(log.get("review_required"),
                            "Fix.Bug should be flagged for review in skill mode")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
