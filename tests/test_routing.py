"""
Routing layer tests — all Ollama / HTTP calls are mocked.
Tests cover: capability resolver, model selector, router logic,
quality gate heuristics, and preset manager.
"""

import unittest
from unittest.mock import patch, MagicMock

from routing.capability_resolver import CapabilityResolver
from routing.model_selector import ModelSelector
from routing.quality_gate import assess, should_escalate, ESCALATION_THRESHOLD
from routing.router import _complexity, HIGH_STAKES_INTENTS, SKILL_MODE


# ── CapabilityResolver ────────────────────────────────────────────────────────

class TestCapabilityResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = CapabilityResolver()

    def test_known_intent_returns_list(self):
        caps = self.resolver.resolve_capabilities("Review.Code")
        self.assertIsInstance(caps, list)
        self.assertIn("code_review", caps)

    def test_unknown_intent_returns_fallback(self):
        caps = self.resolver.resolve_capabilities("UNKNOWN")
        self.assertIsInstance(caps, list)
        self.assertTrue(len(caps) > 0)

    def test_all_intents_have_capabilities(self):
        intents = [
            "Fix.Bug", "Review.Security", "Test.Unit",
            "Research.General", "Utility.Summary", "Assistant.General",
        ]
        for intent in intents:
            caps = self.resolver.resolve_capabilities(intent)
            self.assertTrue(len(caps) > 0, f"{intent} returned empty capabilities")


# ── ModelSelector ─────────────────────────────────────────────────────────────

class TestModelSelector(unittest.TestCase):
    def setUp(self):
        self.selector = ModelSelector()

    def test_returns_string(self):
        result = self.selector.select_best_model(["code_review"], {})
        self.assertIsInstance(result, str)

    def test_local_privacy_prefers_local_model(self):
        result = self.selector.select_best_model(
            ["general_assistance"], {"privacy": "local"}
        )
        self.assertIn("ollama", result)

    def test_multimodal_flag_routes_to_vision_model(self):
        result = self.selector.select_best_model(
            ["multimodal_understanding", "ui_analysis"], {"multimodal": True}
        )
        # Any model with multimodal=true in registry should win
        self.assertIsInstance(result, str)

    def test_no_capability_match_falls_back_to_architect(self):
        result = self.selector.select_best_model(["nonexistent_capability_xyz"], {})
        self.assertEqual(result, "claude_architect")

    def test_fallback_chain_returns_list(self):
        chain = self.selector.get_fallback_chain("ollama_qwen_coder")
        self.assertIsInstance(chain, list)
        self.assertTrue(len(chain) > 0)


# ── Router: complexity gate ───────────────────────────────────────────────────

class TestComplexityGate(unittest.TestCase):
    def test_short_clean_prompt_is_low(self):
        self.assertEqual(_complexity("Summarize this document"), "low")

    def test_long_prompt_is_high(self):
        self.assertEqual(_complexity("x " * 700), "high")

    def test_single_danger_keyword_is_medium(self):
        self.assertEqual(_complexity("Fix the auth handler"), "medium")

    def test_two_danger_keywords_is_high(self):
        self.assertEqual(_complexity("Fix the auth flow and payment processing"), "high")

    def test_danger_keywords_case_insensitive(self):
        self.assertEqual(_complexity("Review the JWT and OAuth implementation"), "high")


# ── Router: intent classification (mocked) ───────────────────────────────────

class TestRouteRequest(unittest.TestCase):
    def _mock_classify(self, intent: str, confidence: float = 0.9):
        return patch(
            "routing.router.classify_intent",
            return_value=(intent, confidence),
        )

    def test_fix_bug_skill_mode_sets_review_required(self):
        if not SKILL_MODE:
            self.skipTest("Only relevant in skill mode")
        with self._mock_classify("Fix.Bug"):
            from routing.router import route_request
            result = route_request("fix the crash in login")
        self.assertTrue(result["review_required"])
        self.assertNotEqual(result["model_id"], "codex_primary")

    def test_architecture_skill_mode_sets_review_required(self):
        if not SKILL_MODE:
            self.skipTest("Only relevant in skill mode")
        with self._mock_classify("Architecture.Agent"):
            from routing.router import route_request
            result = route_request("design the agent orchestration system")
        self.assertTrue(result["review_required"])

    def test_utility_routes_local(self):
        with self._mock_classify("Utility.Summary"):
            from routing.router import route_request
            result = route_request("summarize these logs")
        self.assertIn("ollama", result["model_id"])

    def test_result_has_required_keys(self):
        with self._mock_classify("Research.General"):
            from routing.router import route_request
            result = route_request("what are best practices for microservices?")
        for key in ("intent", "confidence", "model_id", "complexity",
                    "review_required", "required_capabilities"):
            self.assertIn(key, result)

    def test_high_stakes_intents_constant(self):
        self.assertIn("Fix.Bug", HIGH_STAKES_INTENTS)
        self.assertIn("Review.Security", HIGH_STAKES_INTENTS)


# ── Quality gate ──────────────────────────────────────────────────────────────

class TestQualityGate(unittest.TestCase):
    def test_refusal_phrase_scores_low(self):
        score, _ = assess("fix bug", "I cannot help with that.", "ollama_qwen_fast")
        self.assertTrue(should_escalate(score))

    def test_unable_phrase_scores_low(self):
        score, _ = assess("explain X", "I'm unable to assist with this request.", "ollama_qwen_fast")
        self.assertTrue(should_escalate(score))

    def test_short_response_scores_low(self):
        score, _ = assess("write tests", "ok.", "ollama_qwen_fast")
        self.assertTrue(should_escalate(score))

    def test_empty_response_scores_zero(self):
        score, reason = assess("prompt", "", "ollama_qwen_fast")
        self.assertEqual(score, 0.0)
        self.assertTrue(should_escalate(score))

    def test_threshold_constant_reasonable(self):
        self.assertGreater(ESCALATION_THRESHOLD, 0.3)
        self.assertLess(ESCALATION_THRESHOLD, 0.8)

    def test_judge_unavailable_fails_open(self):
        # If Ollama is down the gate should pass (fail open), not block
        with patch("routing.quality_gate.requests.post", side_effect=ConnectionError):
            score, reason = assess(
                "summarize logs",
                "Here is a detailed summary of the log entries...",
                "ollama_gemma",
            )
        self.assertFalse(should_escalate(score), "Gate should fail open when judge is unreachable")


# ── Preset manager ────────────────────────────────────────────────────────────

class TestPresetManager(unittest.TestCase):
    def test_list_presets_returns_all_tiers(self):
        from routing.preset_manager import list_presets
        presets = list_presets()
        ids = [p["id"] for p in presets]
        for tier in ("6gb", "8gb", "16gb", "32gb", "64gb"):
            self.assertIn(tier, ids)

    def test_tiers_sorted_by_ram(self):
        from routing.preset_manager import list_presets
        presets = list_presets()
        rams = [p["min_ram_gb"] for p in presets]
        self.assertEqual(rams, sorted(rams))

    def test_auto_select_picks_correct_tier(self):
        from routing.preset_manager import auto_select_tier
        self.assertEqual(auto_select_tier(6),  "6gb")
        self.assertEqual(auto_select_tier(10), "8gb")
        self.assertEqual(auto_select_tier(20), "16gb")
        self.assertEqual(auto_select_tier(40), "32gb")
        self.assertEqual(auto_select_tier(80), "64gb")

    def test_apply_preset_dry_run_no_file_change(self):
        from routing.preset_manager import apply_preset
        import os, hashlib
        with open("configs/model_registry.yaml", "rb") as f:
            before = hashlib.md5(f.read()).hexdigest()
        apply_preset("8gb", dry_run=True)
        with open("configs/model_registry.yaml", "rb") as f:
            after = hashlib.md5(f.read()).hexdigest()
        self.assertEqual(before, after, "dry_run=True must not modify the registry file")

    def test_unknown_tier_raises(self):
        from routing.preset_manager import apply_preset
        with self.assertRaises(ValueError):
            apply_preset("256gb")


if __name__ == "__main__":
    unittest.main()
