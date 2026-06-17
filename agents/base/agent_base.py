import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base for all Godmode agents that require an external API key."""

    def __init__(self, model_id: str, api_key_env_var: str) -> None:
        self.model_id = model_id
        self.api_key = os.getenv(api_key_env_var)

        if not self.api_key:
            logger.error(f"Missing required environment variable: {api_key_env_var}")
            raise EnvironmentError(f"Required API key '{api_key_env_var}' is not set.")

        logger.info(f"Initialized {self.__class__.__name__} with model: {self.model_id}")

    def _validate_input(self, prompt: str) -> None:
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty, None, or non-string type")

    @abstractmethod
    def execute(self, prompt: str, context: dict | None = None) -> str:
        """Core execution logic to be implemented by subclasses."""
        ...

    async def validate_result_async(self, original_prompt: str, result: str) -> tuple[bool, str]:
        """Default pass-through validation; override for agent-specific checks."""
        return True, result

    def log_event(self, message: str, level: str = "info") -> None:
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{self.__class__.__name__}] {message}")
