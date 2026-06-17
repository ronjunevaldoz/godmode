import logging

import yaml

logger = logging.getLogger(__name__)


class ModelSelector:
    """Selects the best model from the registry based on capability scoring."""

    def __init__(self, registry_path: str = "configs/model_registry.yaml") -> None:
        self.registry_path = registry_path
        self.registry: dict = self._load_registry()

    def _load_registry(self) -> dict:
        with open(self.registry_path) as f:
            return yaml.safe_load(f)

    def select_best_model(self, required_capabilities: list[str], options: dict | None = None) -> str:
        """Ranks candidates and returns the ID of the best-matching model."""
        options = options or {}
        candidates: dict = self.registry.get("models", {})
        best_model_id: str | None = None
        max_score = float("-inf")

        for model_id, meta in candidates.items():
            if not meta.get("enabled", False):
                continue

            score = 0.0
            model_caps = set(meta.get("capabilities", []))
            req_caps = set(required_capabilities)
            matches = req_caps & model_caps

            score += len(matches) * 10.0 if matches else -100.0

            if options.get("privacy") == "local" and meta.get("privacy") == "local":
                score += 50.0
            elif options.get("privacy") == "cloud" and meta.get("privacy") == "cloud":
                score += 10.0

            if options.get("multimodal"):
                score += 50.0 if meta.get("multimodal") else -100.0

            cost_map = {"low": 20.0, "medium": 10.0, "high": 0.0}
            score += cost_map.get(meta.get("cost_tier"), 0.0)

            latency_map = {"low": 15.0, "medium": 5.0, "high": 0.0}
            score += latency_map.get(meta.get("latency_tier"), 0.0)

            score += meta.get("context_window", 0) / 100_000

            if score > max_score:
                max_score = score
                best_model_id = model_id

        if best_model_id is None or max_score < 0:
            return "claude_architect"

        return best_model_id

    def get_fallback_chain(self, model_id: str) -> list[str]:
        return self.registry.get("fallbacks", {}).get(model_id, ["claude_architect"])
