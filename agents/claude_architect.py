import logging
import anthropic
from agents.base.agent_base import BaseAgent

logger = logging.getLogger(__name__)


class ClaudeArchitectAgent(BaseAgent):
    """L3 Governor for high-level reasoning and final validation using Anthropic."""

    def __init__(self, model: str = "claude-opus-4-8") -> None:
        super().__init__(model_id=model, api_key_env_var="ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.async_client = anthropic.AsyncAnthropic(api_key=self.api_key)

    def execute(self, prompt: str, context: dict | None = None) -> str:
        self._validate_input(prompt)
        self.log_event(f"Performing complex reasoning via {self.model_id}")

        try:
            response = self.client.messages.create(
                model=self.model_id,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.content[0].text
            self.log_event("Reasoning task completed successfully")
            return result
        except Exception as e:
            self.log_event(f"Execution failed: {e}", "error")
            raise

    async def validate_result_async(
        self, original_prompt: str, specialist_result: str
    ) -> tuple[bool, str]:
        self._validate_input(original_prompt)
        self.log_event("Starting L3 validation process...")

        validation_query = (
            f"Review this output against the original intent.\n\n"
            f"Original Prompt: {original_prompt}\n"
            f"Specialist Output: {specialist_result}\n\n"
            f"Is it accurate? Provide a brief assessment."
        )

        try:
            response = await self.async_client.messages.create(
                model=self.model_id,
                max_tokens=1024,
                messages=[{"role": "user", "content": validation_query}],
            )
            assessment = response.content[0].text
            self.log_event("Validation complete.")
            return True, f"{specialist_result}\n\n--- ARCHITECT ASSESSMENT ---\n{assessment}"
        except Exception as e:
            self.log_event(f"Validation error: {e}", "error")
            return False, specialist_result
