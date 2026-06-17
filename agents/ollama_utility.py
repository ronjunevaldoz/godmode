import logging
import os
from typing import Final

import requests

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL: Final = os.getenv(
    "OLLAMA_BASE_URL", "http://localhost:11434/api/chat"
)

ROLE_PROMPTS: Final[dict[str, str]] = {
    "code_review": (
        "You are a senior code reviewer. Analyze for bugs, security vulnerabilities, "
        "performance issues, and style violations. Be specific and actionable. "
        "Format findings as a numbered list with severity labels."
    ),
    "unit_test": (
        "You are a test engineering specialist. Generate comprehensive unit tests "
        "with proper assertions, edge cases, and realistic mocks. "
        "Use the same language and framework as the input code."
    ),
    "bug_fix": (
        "You are a debugging specialist. Identify the root cause, provide a minimal "
        "correct fix, and explain why the bug occurred."
    ),
    "security_audit": (
        "You are a security researcher. Identify vulnerabilities, classify them by "
        "OWASP category and severity (Critical / High / Medium / Low), "
        "and provide concrete remediation steps."
    ),
    "research": (
        "You are a technical research analyst. Synthesize information clearly, "
        "structure your analysis, and provide evidence-based conclusions."
    ),
    "prompt_quality": (
        "You are a prompt engineering expert. Analyze the given prompt for clarity, "
        "specificity, and effectiveness. Rewrite it to be more precise and likely to "
        "elicit the desired response. Show before/after."
    ),
    "code_improvement": (
        "You are a senior software architect. Suggest concrete, actionable improvements "
        "for code quality, readability, maintainability, performance, and testability."
    ),
    "assistant": "You are a helpful and knowledgeable AI assistant. Answer clearly and concisely.",
    "vision": "You are a visual analysis assistant. Describe and analyze images or UI screens in detail.",
    "classification": "You are a classification system. Analyze the input and return a structured classification result.",
    "summarization": "You are a summarization expert. Provide clear, accurate summaries that capture key points.",
    "documentation": "You are a technical writer. Create clear, well-structured documentation.",
}


LOCAL_MODEL_ROLES: dict[str, str] = {
    "qwen3-coder:30b":   "code review · bug fix · unit tests",
    "deepseek-r1:14b":   "audit · security · prompt quality",
    "gemma4:12b":        "research · docs · analysis",
    "qwen3:8b":          "assistant · classification",
    "qwen2.5-coder:14b": "code tasks (legacy)",
    "llava:latest":      "vision · UI",
}


class OllamaUtilityAgent:
    """Local Ollama specialist — zero API cost, role-specialized via system prompt."""

    # Token counts from the last execute() call (set after each request)
    last_prompt_tokens: int = 0
    last_completion_tokens: int = 0

    def __init__(self, model: str = "qwen3:8b", role: str = "assistant") -> None:
        self.model = model
        self.role = role
        self._system_prompt = ROLE_PROMPTS.get(role, ROLE_PROMPTS["assistant"])
        logger.info(f"Initialized OllamaUtilityAgent model={self.model} role={self.role}")

    def execute(self, prompt: str, context: dict | None = None) -> str:
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty, None, or non-string type")

        logger.info(f"[Ollama:{self.role}] Sending to {self.model}...")
        try:
            response = requests.post(
                OLLAMA_BASE_URL,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self._system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()

            # Extract actual token counts (Ollama provides these)
            self.last_prompt_tokens = data.get("prompt_eval_count", 0)
            self.last_completion_tokens = data.get("eval_count", 0)

            # Fallback to character estimate if Ollama didn't return counts
            if not self.last_prompt_tokens:
                self.last_prompt_tokens = len(prompt) // 4
            if not self.last_completion_tokens:
                result_text = data["message"]["content"]
                self.last_completion_tokens = len(result_text) // 4

            result: str = data["message"]["content"]
            logger.info(
                f"[Ollama:{self.role}] Done. "
                f"tokens in={self.last_prompt_tokens} out={self.last_completion_tokens}"
            )
            return result
        except Exception as e:
            logger.error(f"OllamaUtilityAgent({self.role}).execute failed: {e}")
            raise

    async def validate_result_async(self, original_prompt: str, result: str) -> tuple[bool, str]:
        return True, result
