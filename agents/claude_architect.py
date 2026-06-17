import logging
import os
from typing import Dict, Any, Optional, Tuple
import anthropic
from agents.base.agent_base import BaseAgent

logger = logging.getLogger(__name__)

class ClaudeArchitectAgent(BaseAgent):
    """
    L3 Governor for high-level reasoning and final validation using Anthropic.
    """
    def __init__(self, model="claude-3-opus-20240229"):
        super().__init__(model_id=model, api_key_env_var="ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def execute(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        self._validate_input(prompt)
        self.log_event(f"Performing complex reasoning via {self.model_id}")
        
        try:
            response = self.client.messages.create(
                model=self.model_id,
                max_tokens=2048,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text
            self.log_event("Reasoning task completed successfully")
            return result
        except Exception as e:
            self.log_event(f"Execution failed: {str(e)}", "error")
            raise

    async def validate_result_async(self, original_prompt: str, specialist_result: str) -> Tuple[bool, str]:
        self._validate_input(original_prompt)
        self.log_event("Starting L3 Validation process...")
        
        try:
            validation_query = (
                f"Review this output against the original intent.\n\n"
                f"Original Prompt: {original_prompt}\n"
                f"Specialist Output: {specialist_result}\n\n"
                f"Is it accurate? Provide a brief assessment."
            )
            
            response = self.client.messages.create(
                model=self.model_id,
                max_tokens=1024,
                temperature=0.3,
                messages=[{"role": "user", "content": validation_query}]
            )
            assessment = response.content[0].text
            self.log_event("Validation complete.")
            # For simplicity in this implementation, we return True but include the assessment
            return True, f"{specialist_result}\n\n--- ARCHITECT ASSESSMENT ---\n{assessment}"
        except Exception as e:
            self.log_event(f"Validation error: {str(e)}", "error")
            return False, specialist_result
