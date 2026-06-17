import logging
import openai
from agents.base.agent_base import BaseAgent

logger = logging.getLogger(__name__)


class CodexEngineerAgent(BaseAgent):
    """L2 Specialist for implementation-heavy code tasks using OpenAI."""

    def __init__(self, model: str = "gpt-4o") -> None:
        super().__init__(model_id=model, api_key_env_var="OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.api_key)

    def execute(self, prompt: str, context: dict | None = None) -> str:
        self._validate_input(prompt)
        self.log_event(f"Processing task via {self.model_id}")

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior software engineer specializing in clean, production-ready code.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2048,
            )
            result = response.choices[0].message.content
            self.log_event("Task completed successfully")
            return result
        except Exception as e:
            self.log_event(f"Execution failed: {e}", "error")
            raise

    async def validate_result_async(
        self, original_prompt: str, result: str
    ) -> tuple[bool, str]:
        if not result or len(result) < 10:
            return False, f"Result too short to be valid: {result}"
        return True, result
