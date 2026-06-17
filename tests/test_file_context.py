"""
Tests for --file flag and _build_file_context() introduced in the
explicit file context refactor (replacing regex-only detection).
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


# ── _build_file_context ───────────────────────────────────────────────────────

class TestBuildFileContext(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, name: str, content: str) -> Path:
        p = self.tmp_path / name
        p.write_text(content)
        return p

    def test_explicit_file_injected(self):
        f = self._write("Auth.kt", "class Auth {}")
        from main import _build_file_context
        result = _build_file_context("security review", [str(f)])
        self.assertIn('<file path=', result)
        self.assertIn("class Auth {}", result)
        self.assertIn("security review", result)

    def test_explicit_file_content_before_prompt(self):
        f = self._write("Foo.py", "def foo(): pass")
        from main import _build_file_context
        result = _build_file_context("find bugs", [str(f)])
        self.assertLess(result.index("def foo()"), result.index("find bugs"))

    def test_multiple_explicit_files_all_injected(self):
        f1 = self._write("Old.kt", "class Old {}")
        f2 = self._write("New.kt", "class New {}")
        from main import _build_file_context
        result = _build_file_context("compare", [str(f1), str(f2)])
        self.assertIn("class Old {}", result)
        self.assertIn("class New {}", result)

    def test_missing_explicit_file_warns_and_continues(self):
        f = self._write("Real.kt", "class Real {}")
        from main import _build_file_context
        import io
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            result = _build_file_context("review", [str(f), "/nonexistent/Missing.kt"])
        output = mock_out.getvalue()
        self.assertIn("not found", output)
        self.assertIn("class Real {}", result)

    def test_no_files_no_injection(self):
        from main import _build_file_context
        result = _build_file_context("explain SOLID principles", [])
        self.assertEqual(result, "explain SOLID principles")

    def test_bare_class_name_no_injection(self):
        from main import _build_file_context
        result = _build_file_context("review SalaryServiceImpl", [])
        self.assertEqual(result, "review SalaryServiceImpl")
        self.assertNotIn("<file", result)

    def test_regex_fallback_injects_path_in_prompt(self):
        f = self._write("parser.py", "def parse(): pass")
        from main import _build_file_context
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(self.tmp_path)
            result = _build_file_context("review parser.py", [])
        finally:
            os.chdir(orig_cwd)
        self.assertIn("def parse(): pass", result)

    def test_deduplication_explicit_and_regex(self):
        """Same file passed via --file and mentioned in prompt — injected once."""
        f = self._write("auth.py", "def login(): pass")
        from main import _build_file_context
        import os
        orig_cwd = os.getcwd()
        try:
            os.chdir(self.tmp_path)
            result = _build_file_context(f"review {f}", [str(f)])
        finally:
            os.chdir(orig_cwd)
        self.assertEqual(result.count("def login(): pass"), 1)

    def test_file_content_truncated_at_max_chars(self):
        large_content = "A" * 20_000
        f = self._write("large.py", large_content)
        from main import _build_file_context, _MAX_FILE_CHARS
        result = _build_file_context("review", [str(f)])
        # Full 20k content must not be present; truncated slice should be
        self.assertNotIn("A" * 20_000, result)
        self.assertIn("A" * _MAX_FILE_CHARS, result)


# ── cmd_run flag parsing ──────────────────────────────────────────────────────

class TestCmdRunFlagParsing(unittest.TestCase):

    def _run(self, args, mock_orchestrate):
        with patch("main.orchestrate", mock_orchestrate):
            from godmode_cli import cmd_run
            cmd_run(args)

    def test_file_flag_passed_to_orchestrate(self):
        mock = MagicMock()
        self._run(["find bugs", "--file", "src/Foo.kt"], mock)
        mock.assert_called_once_with("find bugs", session=None, files=["src/Foo.kt"])

    def test_multiple_file_flags(self):
        mock = MagicMock()
        self._run(["compare", "--file", "old.kt", "--file", "new.kt"], mock)
        mock.assert_called_once_with("compare", session=None, files=["old.kt", "new.kt"])

    def test_file_and_session_together(self):
        mock = MagicMock()
        self._run(["security review", "--file", "Auth.kt", "--session", "myproject"], mock)
        mock.assert_called_once_with(
            "security review", session="myproject", files=["Auth.kt"]
        )

    def test_no_file_flag_passes_none(self):
        mock = MagicMock()
        self._run(["explain SOLID"], mock)
        mock.assert_called_once_with("explain SOLID", session=None, files=None)

    def test_no_prompt_exits(self):
        mock = MagicMock()
        with self.assertRaises(SystemExit):
            self._run(["--file", "Foo.kt"], mock)

    def test_prompt_words_joined(self):
        mock = MagicMock()
        self._run(["find", "all", "bugs"], mock)
        mock.assert_called_once_with("find all bugs", session=None, files=None)

    def test_file_flag_before_prompt_words(self):
        mock = MagicMock()
        self._run(["--file", "Foo.kt", "security review"], mock)
        mock.assert_called_once_with("security review", session=None, files=["Foo.kt"])


# ── orchestrate files parameter ───────────────────────────────────────────────

class TestOrchestrateFilesParam(unittest.TestCase):

    @patch("main._build_file_context")
    @patch("main.route_request")
    @patch("main.run_with_retry")
    @patch("main.quality_assess")
    @patch("main.adapter")
    @patch("main.memory")
    def test_files_forwarded_to_build_file_context(
        self, mock_mem, mock_adapter, mock_qa, mock_retry, mock_route, mock_build
    ):
        mock_route.return_value = {
            "intent": "Utility.Summarize", "decision": "LOCAL",
            "model_id": "ollama_qwen_fast", "complexity": "low",
            "confidence": 0.9, "escalation_reason": None, "review_required": False,
        }
        mock_build.return_value = "enriched prompt"
        mock_retry.return_value = ("result", True, False)
        mock_qa.return_value = (0.9, "good")
        mock_adapter.get_token_counts.return_value = (100, 50)

        from main import orchestrate
        orchestrate("summarize this", files=["src/Foo.kt"])

        mock_build.assert_called_once_with("summarize this", ["src/Foo.kt"])

    @patch("main._build_file_context")
    @patch("main.route_request")
    @patch("main.run_with_retry")
    @patch("main.quality_assess")
    @patch("main.adapter")
    @patch("main.memory")
    def test_no_files_passes_empty_list(
        self, mock_mem, mock_adapter, mock_qa, mock_retry, mock_route, mock_build
    ):
        mock_route.return_value = {
            "intent": "Utility.Summarize", "decision": "LOCAL",
            "model_id": "ollama_qwen_fast", "complexity": "low",
            "confidence": 0.9, "escalation_reason": None, "review_required": False,
        }
        mock_build.return_value = "prompt"
        mock_retry.return_value = ("result", True, False)
        mock_qa.return_value = (0.9, "good")
        mock_adapter.get_token_counts.return_value = (100, 50)

        from main import orchestrate
        orchestrate("summarize this")

        mock_build.assert_called_once_with("summarize this", [])


if __name__ == "__main__":
    unittest.main()
