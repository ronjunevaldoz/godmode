from typing import Any, Dict
from agents.ollama_utility import OllamaUtilityAgent
from agents.codex_engineer import CodexEngineerAgent
from agents.gemini_vision import GeminiVisionAgent
from agents.claude_architect import ClaudeArchitectAgent

class ProviderAdapter:
    """
    Bridges the Model Registry's model_ids to the actual Agent implementations.
    """
    def __init__(self):
        # Map registry IDs to their corresponding Agent classes
        self._model_to_agent_map = {
            "codex_primary": CodexEngineerAgent(),
            "claude_architect": ClaudeArchitectAgent(),
            "gemini_vision": GeminiVisionAgent(),
            "ollama_qwen": OllamaUtilityAgent(),
        }

    def execute(self, model_id: str, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Finds the agent mapped to the model_id and executes the request.
        """
        agent = self._model_to_agent_map.get(model_id)

        if not agent:
            raise ValueError(f"No agent implementation found for model ID: {model_id}")

        return agent.execute(prompt, context)

    def validate_result(self, model_id: str, original_prompt: str, result: str) -> Tuple[bool, str]:
        """
        Special case for validation. Since only Claude currently validates,
        we route this to the Claude Architect agent.
        """
        # Even if the model_id is not Claude, validation is a Claude-tier task
        validator = self._model_to_agent_map.get("claude_architect")
        if not validator:
            return True, result # Fallback: assume valid if no validator exists

        return validator.validate_result(original_prompt, result)
