import logging
import os

import requests

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api/chat")


class OllamaUtilityAgent:
    """L2 Specialist for cheap, local, repetitive tasks via Ollama."""

    def __init__(self, model: str = "llama3") -> None:
        self.model = model
        logger.info(f"Initialized OllamaUtilityAgent with model: {self.model}")

    def execute(self, prompt: str, context: dict | None = None) -> str:
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty, None, or non-string type")

        logger.info(f"[L2-Ollama] Processing utility task using {self.model}...")
        try:
            response = requests.post(
                OLLAMA_BASE_URL,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=30,
            )
            response.raise_for_status()
            result: str = response.json()["message"]["content"]
            logger.info("Utility task completed successfully")
            return result
        except Exception as e:
            logger.error(f"OllamaUtilityAgent.execute failed: {e}")
            raise

    async def validate_result_async(self, original_prompt: str, result: str) -> tuple[bool, str]:
        return True, result
