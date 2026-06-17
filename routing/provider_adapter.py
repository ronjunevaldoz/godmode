import logging
from typing import Any, Callable

from agents.ollama_utility import OllamaUtilityAgent

logger = logging.getLogger(__name__)

# Cloud agent imports are deferred inside factories to avoid EnvironmentError
# at import time when API keys are not set.


def _make_codex() -> Any:
    from agents.codex_engineer import CodexEngineerAgent
    return CodexEngineerAgent()


def _make_claude() -> Any:
    from agents.claude_architect import ClaudeArchitectAgent
    return ClaudeArchitectAgent()


def _make_gemini() -> Any:
    from agents.gemini_vision import GeminiVisionAgent
    return GeminiVisionAgent()


# Registry of model_id → factory function
_AGENT_FACTORIES: dict[str, Callable[[], Any]] = {
    # ── Local (free) ──────────────────────────────────────────────────────
    "ollama_qwen_coder": lambda: OllamaUtilityAgent(model="qwen3-coder:30b",  role="code_review"),
    "ollama_deepseek":   lambda: OllamaUtilityAgent(model="deepseek-r1:14b",  role="security_audit"),
    "ollama_gemma":      lambda: OllamaUtilityAgent(model="gemma4:12b",        role="research"),
    "ollama_qwen_fast":  lambda: OllamaUtilityAgent(model="qwen3:8b",          role="assistant"),
    "ollama_llava":      lambda: OllamaUtilityAgent(model="llava:latest",      role="vision"),
    # Legacy alias kept for backward compatibility
    "ollama_qwen":       lambda: OllamaUtilityAgent(model="qwen2.5-coder:14b", role="code_review"),
    # ── Cloud (paid) ──────────────────────────────────────────────────────
    "codex_primary":  _make_codex,
    "claude_architect": _make_claude,
    "gemini_vision":  _make_gemini,
}


class ProviderAdapter:
    """
    Bridges model registry IDs to agent implementations.
    Agents are instantiated lazily — cloud agents only when actually called,
    so missing API keys don't crash the process at startup.
    """

    def __init__(self) -> None:
        self._agents: dict[str, Any] = {}

    def _get_agent(self, model_id: str) -> Any:
        if model_id not in self._agents:
            factory = _AGENT_FACTORIES.get(model_id)
            if not factory:
                raise ValueError(f"No agent implementation for model_id: {model_id!r}")
            self._agents[model_id] = factory()
        return self._agents[model_id]

    def execute(self, model_id: str, prompt: str, context: dict[str, Any] | None = None) -> str:
        agent = self._get_agent(model_id)
        return agent.execute(prompt, context)

    def get_token_counts(self, model_id: str) -> tuple[int, int]:
        """Return (prompt_tokens, completion_tokens) from the last execute() call."""
        agent = self._agents.get(model_id)
        if agent and hasattr(agent, "last_prompt_tokens"):
            return agent.last_prompt_tokens, agent.last_completion_tokens
        return 0, 0

    def validate_result(
        self, model_id: str, original_prompt: str, result: str
    ) -> tuple[bool, str]:
        validator = self._get_agent("claude_architect")
        return validator.validate_result(original_prompt, result)
