import yaml
from typing import List, Dict, Any, Optional

class ModelSelector:
    """
    Selects the best model from the registry based on requirements and scoring.
    """
    def __init__(self, registry_path: str = "configs/model_registry.yaml"):
        self.registry_path = registry_path
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        with open(self.registry_path, "r") as f:
            return yaml.safe_load(f)

    def select_best_model(self, required_capabilities: List[str], options: Dict[str, Any] = None) -> str:
        """
        Ranks candidate models and returns the ID of the best match.
        - options: can contain 'privacy': 'local', 'multimodal': True, etc.
        """
        options = options or {}
        candidates = self.registry.get("models", {})
        best_model_id = None
        max_score = -float('inf')

        for model_id, meta in candidates.items():
            if not meta.get("enabled", False):
                continue

            score = 0.0

            # 1. Capability Match (Critical)
            # Calculate what percentage of required capabilities the model has
            model_caps = set(meta.get("capabilities", []))
            req_caps = set(required_capabilities)
            matches = req_caps.intersection(model_caps)

            if not matches:
                # If the model lacks ANY required capability, it's a poor candidate
                # unless we allow partial matches. For strictness, we penalize heavily.
                score -= 100.0
            else:
                score += len(matches) * 10.0

            # 2. Privacy match (Local-First Policy)
            if options.get("privacy") == "local" and meta.get("privacy") == "local":
                score += 50.0
            elif options.get("privacy") == "cloud" and meta.get("privacy") == "cloud":
                score += 10.0

            # 3. Multimodal support
            if options.get("multimodal") and meta.get("multimodal"):
                score += 50.0
            elif options.get("multimodal") and not meta.get("multimodal"):
                score -= 100.0 # Cannot handle visuals

            # 4. Cost Tier (Prefer lower cost for simple tasks)
            cost_map = {"low": 20.0, "medium": 10.0, "high": 0.0}
            score += cost_map.get(meta.get("cost_tier"), 0.0)

            # 5. Latency Tier (Prefer lower latency)
            latency_map = {"low": 15.0, "medium": 5.0, "high": 0.0}
            score += latency_map.get(meta.get("latency_tier"), 0.0)

            # 6. Context Window (Bigger is generally better, but less weighted)
            score += (meta.get("context_window", 0) / 100000)

            if score > max_score:
                max_score = score
                best_model_id = model_id

        # Fallback if no model scored positively
        if best_model_id is None or max_score < 0:
            return "claude_architect" # Default safety net

        return best_model_id

    def get_fallback_chain(self, model_id: str) -> List[str]:
        return self.registry.get("fallbacks", {}).get(model_id, ["claude_architect"])
