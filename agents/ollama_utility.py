import logging
import os
from typing import Final

import requests

logger = logging.getLogger(__name__)

_OLLAMA_BASE: Final = (
    os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    .rstrip("/")
    .replace("/api/chat", "")
)
OLLAMA_CHAT_URL: Final = f"{_OLLAMA_BASE}/api/chat"

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
    "hf.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF:Q4_K_M": "research · long-context reasoning",
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

    def _build_messages(self, prompt: str, context: dict | None) -> list[dict]:
        messages = [{"role": "system", "content": self._system_prompt}]
        if context and "history" in context:
            history = context["history"]
            if isinstance(history, list):
                valid = [
                    m for m in history
                    if isinstance(m, dict) and "role" in m and "content" in m
                ]
                if len(valid) != len(history):
                    logger.warning(f"[Ollama] Dropped {len(history) - len(valid)} malformed history entries")
                messages.extend(valid)
        messages.append({"role": "user", "content": prompt})
        return messages

    def execute(self, prompt: str, context: dict | None = None, stream: bool = True) -> str:
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty, None, or non-string type")

        messages = self._build_messages(prompt, context)
        logger.info(f"[Ollama:{self.role}] Sending to {self.model} (stream={stream})...")

        try:
            if stream:
                return self._execute_streaming(messages, prompt)
            return self._execute_blocking(messages, prompt)
        except Exception as e:
            logger.error(f"OllamaUtilityAgent({self.role}).execute failed: {e}")
            raise

    def _execute_streaming(self, messages: list[dict], prompt: str) -> str:
        import json as _json
        collected: list[str] = []
        with requests.post(
            OLLAMA_CHAT_URL,
            json={"model": self.model, "messages": messages, "stream": True},
            stream=True,
            timeout=180,
        ) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                chunk = _json.loads(raw_line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    print(token, end="", flush=True)
                    collected.append(token)
                if chunk.get("done"):
                    print()   # newline after last token
                    self.last_prompt_tokens = chunk.get("prompt_eval_count", 0)
                    self.last_completion_tokens = chunk.get("eval_count", 0)

        result = "".join(collected)
        if not self.last_prompt_tokens:
            self.last_prompt_tokens = len(prompt) // 4
        if not self.last_completion_tokens:
            self.last_completion_tokens = len(result) // 4
        logger.info(f"[Ollama:{self.role}] Stream done. tokens in={self.last_prompt_tokens} out={self.last_completion_tokens}")
        return result

    def _execute_blocking(self, messages: list[dict], prompt: str) -> str:
        response = requests.post(
            OLLAMA_CHAT_URL,
            json={"model": self.model, "messages": messages, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()

        self.last_prompt_tokens = data.get("prompt_eval_count", 0)
        self.last_completion_tokens = data.get("eval_count", 0)
        result: str = data["message"]["content"]

        if not self.last_prompt_tokens:
            self.last_prompt_tokens = len(prompt) // 4
        if not self.last_completion_tokens:
            self.last_completion_tokens = len(result) // 4

        logger.info(f"[Ollama:{self.role}] Done. tokens in={self.last_prompt_tokens} out={self.last_completion_tokens}")
        return result

    async def validate_result_async(self, original_prompt: str, result: str) -> tuple[bool, str]:
        return True, result
