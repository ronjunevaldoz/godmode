class OllamaUtilityAgent:
    """
    L2 Specialist for cheap, local, repetitive tasks.
    """
    def __init__(self, model="llama3"):
        self.model = model

    def execute(self, prompt: str, context: dict = None) -> str:
        # Simplified execution logic
        print(f"[L2-Ollama] Processing utility task using {self.model}...")
        # In a real implementation, this would call the Ollama API
        return f"Ollama Utility Response to: {prompt[:50]}..."
