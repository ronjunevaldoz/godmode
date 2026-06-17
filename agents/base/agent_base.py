import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract base class for all Godmode Agents.
    Handles common initialization, validation, and error handling patterns.
    """
    def __init__(self, model_id: str, api_key_env_var: str):
        self.model_id = model_id
        self.api_key = os.getenv(api_key_env_var)
        
        if not self.api_key:
            logger.error(f"Missing required environment variable: {api_key_env_var}")
            raise EnvironmentError(f"Required API key '{api_key_env_var}' is not set.")
            
        logger.info(f"Initialized {self.__class__.__name__} with model: {self.model_id}")

    def _validate_input(self, prompt: str):
        """Common input validation logic."""
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty, None, or non-string type")

    @abstractmethod
    def execute(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Core execution logic to be implemented by subclasses."""
        pass

    async def validate_result_async(self, original_prompt: str, result: str) -> Tuple[bool, str]:
        """Default implementation of result validation (can be overridden)."""
        return True, result

    def log_event(self, message: str, level: str = "info"):
        """Standardized internal event logging."""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{self.__class__.__name__}] {message}")

