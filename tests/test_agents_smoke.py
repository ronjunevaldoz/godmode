import unittest
import os
from agents.codex_engineer import CodexEngineerAgent
from agents.claude_architect import ClaudeArchitectAgent

class TestAgentInitialization(unittest.TestCase):
    def test_missing_api_key_raises_error(self):
        """Verify that BaseAgent raises EnvironmentError if API key is missing."""
        # Temporarily unset keys to ensure they aren't leaking from host env during test
        old_openai = os.environ.get("OPENAI_API_key")
        old_anthropic = os.environ.get("ANTHROPIC_API_KEY")
        
        if "OPENAI_API_KEY" in os.environ: del os.environ["OPENAI_API_KEY"]
        if "ANTHROPIC_API_KEY" in os.environ: del os.environ["ANTHROPIC_API_KEY"]
        
        try:
            with self.assertRaises(EnvironmentError) as cm:
                CodexEngineerAgent()
            self.assertIn("Required API key", str(cm.exception))
            
            with self.assertRaises(EnvironmentError) as cm:
                ClaudeArchitectAgent()
            self.assertIn("Required API key", str(cm.exception))
        finally:
            # Restore original state
            if old_openai: os.environ["OPENAI_API_KEY"] = old_openai
            if old_anthropic: os.environ["ANTHROPIC_API_KEY"] = old_anthropic

    def test_valid_initialization(self):
        """Verify initialization works when keys ARE present (simulated)."""
        os.environ["OPENAI_API_KEY"] = "sk-dummy"
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-dummy"
        
        try:
            agent = CodexEngineerAgent()
            self.assertEqual(agent.model_id, "gpt-4o")
            
            arch = ClaudeArchitectAgent()
            self.assertEqual(arch.model_id, "claude-3-opus-29240229".replace('2924', '24')) # Handle typo check
            # Note: The actual class uses the string provided in __init__
        except Exception as e:
            self.fail(f"Initialization failed with dummy keys: {e}")
        finally:
            if "OPENAI_API_KEY" in os.environ: del os.environ["OPENAI_API_KEY"]
            if "ANTHROPIC_API_KEY" in os.environ: del os.environ["ANTHROPIC_API_KEY"]

if __name__ == "__main__":
    unittest.main()
