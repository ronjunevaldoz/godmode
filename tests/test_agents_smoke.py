import os
import unittest
from unittest.mock import MagicMock, patch

from agents.claude_architect import ClaudeArchitectAgent
from agents.codex_engineer import CodexEngineerAgent
from agents.gemini_vision import GeminiVisionAgent
from agents.ollama_utility import OllamaUtilityAgent


class TestBaseAgentInit(unittest.TestCase):
    def setUp(self):
        self._clear_keys()

    def tearDown(self):
        self._clear_keys()

    def _clear_keys(self):
        for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"):
            os.environ.pop(key, None)

    def test_missing_openai_key_raises(self):
        with self.assertRaises(EnvironmentError) as cm:
            CodexEngineerAgent()
        self.assertIn("Required API key", str(cm.exception))

    def test_missing_anthropic_key_raises(self):
        with self.assertRaises(EnvironmentError) as cm:
            ClaudeArchitectAgent()
        self.assertIn("Required API key", str(cm.exception))

    def test_missing_google_key_raises(self):
        with self.assertRaises(EnvironmentError) as cm:
            GeminiVisionAgent()
        self.assertIn("Required API key", str(cm.exception))

    def test_codex_valid_init(self):
        os.environ["OPENAI_API_KEY"] = "sk-dummy"
        agent = CodexEngineerAgent()
        self.assertEqual(agent.model_id, "gpt-4o")

    def test_claude_valid_init(self):
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-dummy"
        agent = ClaudeArchitectAgent()
        self.assertEqual(agent.model_id, "claude-opus-4-8")

    def test_gemini_valid_init(self):
        os.environ["GOOGLE_API_KEY"] = "gk-dummy"
        agent = GeminiVisionAgent()
        self.assertEqual(agent.model, "gemini-pro-vision")


class TestOllamaUtilityAgent(unittest.TestCase):
    def setUp(self):
        self.agent = OllamaUtilityAgent()

    def test_empty_prompt_raises(self):
        with self.assertRaises(ValueError):
            self.agent.execute("")

    def test_none_prompt_raises(self):
        with self.assertRaises(ValueError):
            self.agent.execute(None)  # type: ignore[arg-type]

    def test_whitespace_prompt_raises(self):
        with self.assertRaises(ValueError):
            self.agent.execute("   ")

    @patch("agents.ollama_utility.requests.post")
    def test_execute_returns_content(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"message": {"content": "hello from ollama"}},
        )
        mock_post.return_value.raise_for_status = MagicMock()
        result = self.agent.execute("summarize this")
        self.assertEqual(result, "hello from ollama")

    @patch("agents.ollama_utility.requests.post")
    def test_execute_raises_on_http_error(self, mock_post):
        import requests as req
        mock_post.return_value.raise_for_status = MagicMock(
            side_effect=req.exceptions.HTTPError("500")
        )
        with self.assertRaises(req.exceptions.HTTPError):
            self.agent.execute("fail prompt")


class TestGeminiVisionAgent(unittest.TestCase):
    def setUp(self):
        os.environ["GOOGLE_API_KEY"] = "gk-dummy"
        self.agent = GeminiVisionAgent()

    def tearDown(self):
        os.environ.pop("GOOGLE_API_KEY", None)

    def test_empty_prompt_raises(self):
        with self.assertRaises(ValueError):
            self.agent.execute("")

    def test_none_prompt_raises(self):
        with self.assertRaises(ValueError):
            self.agent.execute(None)  # type: ignore[arg-type]

    def test_execute_returns_string(self):
        result = self.agent.execute("describe this UI")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


if __name__ == "__main__":
    unittest.main()
