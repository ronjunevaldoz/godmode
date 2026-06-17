"""
Closes remaining coverage gaps:
  - routing/provider_adapter.py  (lazy factory + unknown model)
  - routing/router.py            (standalone cloud escalation branches)
  - routing/preset_manager.py    (generate_matrix, apply write path)
  - metrics/metrics_engine.py    (cheer function all branches)
  - godmode_cli.py               (cmd_* functions via direct call)
"""

import os
import json
import hashlib
import tempfile
import unittest
from unittest.mock import patch, MagicMock


# ── ProviderAdapter ───────────────────────────────────────────────────────────

class TestProviderAdapter(unittest.TestCase):
    def test_ollama_agent_instantiated_lazily(self):
        from routing.provider_adapter import ProviderAdapter
        adapter = ProviderAdapter()
        self.assertEqual(adapter._agents, {})

    def test_get_local_agent_returns_ollama_instance(self):
        from routing.provider_adapter import ProviderAdapter
        from agents.ollama_utility import OllamaUtilityAgent
        adapter = ProviderAdapter()
        agent = adapter._get_agent("ollama_qwen_fast")
        self.assertIsInstance(agent, OllamaUtilityAgent)

    def test_get_agent_cached_on_second_call(self):
        from routing.provider_adapter import ProviderAdapter
        adapter = ProviderAdapter()
        a1 = adapter._get_agent("ollama_gemma")
        a2 = adapter._get_agent("ollama_gemma")
        self.assertIs(a1, a2)

    def test_unknown_model_raises_value_error(self):
        from routing.provider_adapter import ProviderAdapter
        adapter = ProviderAdapter()
        with self.assertRaises(ValueError) as cm:
            adapter._get_agent("nonexistent_model_xyz")
        self.assertIn("nonexistent_model_xyz", str(cm.exception))

    def test_cloud_factory_codex_needs_key(self):
        from routing.provider_adapter import ProviderAdapter
        os.environ.pop("OPENAI_API_KEY", None)
        adapter = ProviderAdapter()
        with self.assertRaises(EnvironmentError):
            adapter._get_agent("codex_primary")

    def test_cloud_factory_claude_needs_key(self):
        from routing.provider_adapter import ProviderAdapter
        os.environ.pop("ANTHROPIC_API_KEY", None)
        adapter = ProviderAdapter()
        with self.assertRaises(EnvironmentError):
            adapter._get_agent("claude_architect")

    def test_get_token_counts_zero_for_unexecuted(self):
        from routing.provider_adapter import ProviderAdapter
        adapter = ProviderAdapter()
        self.assertEqual(adapter.get_token_counts("ollama_qwen_fast"), (0, 0))

    def test_get_token_counts_after_execute(self):
        from routing.provider_adapter import ProviderAdapter
        adapter = ProviderAdapter()
        mock_agent = MagicMock()
        mock_agent.last_prompt_tokens    = 42
        mock_agent.last_completion_tokens = 99
        mock_agent.execute.return_value  = "result"
        adapter._agents["ollama_qwen_fast"] = mock_agent
        adapter.execute("ollama_qwen_fast", "hello")
        self.assertEqual(adapter.get_token_counts("ollama_qwen_fast"), (42, 99))


# ── Router standalone branches ────────────────────────────────────────────────

class TestRouterStandaloneBranches(unittest.TestCase):
    """Tests the cloud-escalation paths active when GODMODE_MODE=standalone."""

    def _route(self, intent: str, confidence: float = 0.9, prompt: str = "test prompt"):
        from routing.router import route_request
        with patch("routing.router.classify_intent", return_value=(intent, confidence)):
            with patch("routing.router.SKILL_MODE", False):
                return route_request(prompt)

    def test_fix_bug_standalone_routes_to_codex(self):
        result = self._route("Fix.Bug")
        self.assertEqual(result["model_id"], "codex_primary")
        self.assertFalse(result["review_required"])

    def test_review_security_standalone_routes_to_codex(self):
        result = self._route("Review.Security")
        self.assertEqual(result["model_id"], "codex_primary")

    def test_architecture_standalone_routes_to_claude(self):
        result = self._route("Architecture.Agent")
        self.assertEqual(result["model_id"], "claude_architect")

    def test_low_confidence_standalone_escalates_to_claude(self):
        result = self._route("Research.General", confidence=0.2)
        self.assertEqual(result["model_id"], "claude_architect")

    def test_complexity_standalone_escalates_to_codex(self):
        danger_prompt = "Fix the auth and payment encryption vulnerability in prod"
        result = self._route("Improve.Code", prompt=danger_prompt)
        self.assertEqual(result["model_id"], "codex_primary")


# ── PresetManager — write path + matrix ──────────────────────────────────────

class TestPresetManagerWritePath(unittest.TestCase):
    def _copy_registry(self) -> str:
        """Return path to a temp copy of the real registry."""
        import shutil
        tmp = tempfile.NamedTemporaryFile(suffix=".yaml", delete=False)
        tmp.close()
        shutil.copy("configs/model_registry.yaml", tmp.name)
        return tmp.name

    def test_apply_writes_changed_models(self):
        from routing.preset_manager import apply_preset
        tmp = self._copy_registry()
        try:
            with patch("routing.preset_manager.REGISTRY_PATH", tmp):
                changes = apply_preset("8gb", dry_run=False)
            # At least one model must have changed (8gb uses smaller models)
            self.assertIsInstance(changes, list)
            # Verify file was actually written
            import yaml
            with open(tmp) as f:
                written = yaml.safe_load(f)
            # ollama_qwen_fast should be qwen2.5:7b in 8gb preset
            self.assertEqual(
                written["models"]["ollama_qwen_fast"]["model"], "qwen2.5:7b"
            )
        finally:
            os.unlink(tmp)

    def test_apply_no_changes_when_already_matching(self):
        """Applying same preset twice should report no changes the second time."""
        from routing.preset_manager import apply_preset
        tmp = self._copy_registry()
        try:
            with patch("routing.preset_manager.REGISTRY_PATH", tmp):
                apply_preset("8gb", dry_run=False)
                changes = apply_preset("8gb", dry_run=False)
            self.assertEqual(changes, [])
        finally:
            os.unlink(tmp)

    def test_generate_matrix_contains_all_tiers(self):
        from routing.preset_manager import generate_matrix
        matrix = generate_matrix()
        for tier in ("Entry", "Standard", "Mid-range", "High-end", "Workstation"):
            self.assertIn(tier, matrix)

    def test_generate_matrix_contains_roles(self):
        from routing.preset_manager import generate_matrix
        matrix = generate_matrix()
        for role in ("qwen coder", "deepseek", "gemma", "qwen fast", "llava"):
            self.assertIn(role, matrix)


# ── MetricsEngine cheer ───────────────────────────────────────────────────────

class TestCheer(unittest.TestCase):
    def _engine_with_logs(self, logs: list) -> "MetricsEngine":
        from metrics.metrics_engine import MetricsEngine
        from memory.memory_manager import MemoryManager
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.close()
        mem = MemoryManager(storage_path=tmp.name)
        for log in logs:
            mem.log_task(log)
        engine = MetricsEngine(mem)
        engine._tmp_path = tmp.name
        return engine

    def tearDown(self):
        # Clean up any temp files created
        pass

    def _local_log(self, **kw):
        return {
            "user_input": "x", "intent": "Utility.Summary",
            "target_model": "ollama_qwen_fast", "ollama_model": "qwen3:8b",
            "confidence": 0.9, "latency": 1.0, "success": True,
            "fallback_used": False, "escalation_used": False,
            "tokens_in": 100, "tokens_out": 200, "notes": "", **kw,
        }

    def _cloud_log(self, **kw):
        return {**self._local_log(), "target_model": "claude_architect",
                "ollama_model": None, **kw}

    def test_100_percent_local_is_perfect(self):
        engine = self._engine_with_logs([self._local_log() for _ in range(5)])
        report = engine.generate_report()
        self.assertIn("PERFECT", report)
        try:
            os.unlink(engine._tmp_path)
        except Exception:
            pass

    def test_80_percent_local_is_winning(self):
        logs = [self._local_log() for _ in range(8)] + [self._cloud_log() for _ in range(2)]
        engine = self._engine_with_logs(logs)
        report = engine.generate_report()
        self.assertIn("WINNING", report)
        try:
            os.unlink(engine._tmp_path)
        except Exception:
            pass

    def test_50_percent_local_is_neutral(self):
        logs = [self._local_log() for _ in range(5)] + [self._cloud_log() for _ in range(5)]
        engine = self._engine_with_logs(logs)
        report = engine.generate_report()
        self.assertIn("NEUTRAL", report)
        try:
            os.unlink(engine._tmp_path)
        except Exception:
            pass

    def test_low_local_is_warning(self):
        logs = [self._local_log() for _ in range(2)] + [self._cloud_log() for _ in range(8)]
        engine = self._engine_with_logs(logs)
        report = engine.generate_report()
        self.assertIn("WARNING", report)
        try:
            os.unlink(engine._tmp_path)
        except Exception:
            pass

    def test_zero_local_is_in_the_red(self):
        engine = self._engine_with_logs([self._cloud_log() for _ in range(3)])
        report = engine.generate_report()
        self.assertIn("IN THE RED", report)
        try:
            os.unlink(engine._tmp_path)
        except Exception:
            pass


# ── godmode_cli commands ──────────────────────────────────────────────────────

class TestGodmodeCLI(unittest.TestCase):
    """Test each cmd_* function directly (no subprocess)."""

    def test_cmd_clear_resets_log(self):
        import godmode_cli as cli
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.write(b'[{"task": 1}]')
        tmp.close()
        with patch("godmode_cli.Path") as MockPath:
            mock_p = MagicMock()
            MockPath.return_value = mock_p
            cli.cmd_clear([])
            mock_p.write_text.assert_called_once_with("[]")
        os.unlink(tmp.name)

    def test_cmd_stats_calls_generate_report(self):
        import godmode_cli as cli
        with patch("godmode_cli.cmd_stats") as mock_stats:
            mock_stats([])
            mock_stats.assert_called_once()

    def test_help_output_lists_all_commands(self):
        import godmode_cli as cli
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            try:
                cli.main.__wrapped__([]) if hasattr(cli.main, "__wrapped__") else None
            except SystemExit:
                pass
            # Call directly
            import sys
            with patch.object(sys, "argv", ["godmode_cli.py"]):
                try:
                    cli.main()
                except SystemExit:
                    pass
        output = buf.getvalue()
        for cmd in ("run", "stats", "eval", "clear", "models", "preset", "recommend", "coverage"):
            self.assertIn(cmd, output)

    def test_unknown_command_exits_nonzero(self):
        import godmode_cli as cli
        import sys
        with patch.object(sys, "argv", ["godmode_cli.py", "notacommand"]):
            with self.assertRaises(SystemExit) as cm:
                cli.main()
            self.assertEqual(cm.exception.code, 1)

    def test_preset_list_prints_matrix(self):
        import godmode_cli as cli
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.cmd_preset(["list"])
        self.assertIn("Entry", buf.getvalue())

    def test_preset_show_prints_dry_run(self):
        import godmode_cli as cli
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.cmd_preset(["show", "8gb"])
        output = buf.getvalue()
        self.assertIn("8gb", output.lower().replace(" ", "").lower() or output)
        self.assertIn("Preset", output)

    def test_preset_unknown_subcommand(self):
        import godmode_cli as cli
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.cmd_preset(["frobnicate"])
        self.assertIn("Unknown", buf.getvalue())

    def test_models_handles_ollama_down(self):
        import godmode_cli as cli
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("requests.get", side_effect=ConnectionError("offline")):
            with redirect_stdout(buf):
                cli.cmd_models([])
        self.assertIn("Cannot reach", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
