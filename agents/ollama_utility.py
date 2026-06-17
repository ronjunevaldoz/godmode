import logging

# Set up logging
logger = logging.getLogger(__name__)

class OllamaUtilityAgent:
    """
    L2 Specialist for cheap, local, repetitive tasks.
    """
    def __init__(self, model="llama3"):
        self.model = model
        logger.info(f"Initialized OllamaUtilityAgent with model: {self.model}")

    def execute(self, prompt: str, context: dict = None) -> str:
        """
        Processes utility tasks using the Ollama model.
        
        Args:
            prompt (str): The input prompt for utility task
            context (dict, optional): Additional context for processing
            
        Returns:
            str: The utility response
            
        Raises:
            ValueError: If prompt is empty or None
        """
        if not prompt:
            raise ValueError("Prompt cannot be empty or None")
            
        logger.info(f"[L2-Ollama] Processing utility task using {self.model}...")
        try:
            # Simplified execution logic
            # In a real implementation, this would call the Ollama API
            result = f"Ollama Utility Response to: {prompt[:50]}..."
            logger.info("Utility task completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error in OllamaUtilityAgent.execute: {str(e)}")
            raise