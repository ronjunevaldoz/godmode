import yaml
from typing import List, Dict, Any

class RegistryValidator:
    """
    Validates the Model Registry for consistency and correctness.
    """
    def __init__(self, registry_path: str = "configs/model_registry.yaml"):
        self.registry_path = registry_path

    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        try:
            with open(self.registry_path, "r") as f:
                registry = yaml.safe_load(f)
        except Exception as e:
            return False, [f"YAML Load Error: {e}"]

        models = registry.get("models", {})
        fallbacks = registry.get("fallbacks", {})

        if not models:
            errors.append("Registry contains no models.")

        # Check models
        for model_id, meta in models.items():
            # Check basic fields
            required_fields = ["provider", "model", "capabilities", "enabled"]
            for field in required_fields:
                if field not in meta:
                    errors.append(f"Model {model_id} is missing required field: {field}")

            # Validate capabilities list
            if not isinstance(meta.get("capabilities"), list):
                errors.append(f"Model {model_id} capabilities must be a list.")

        # Validate fallbacks
        for model_id, fallback_list in fallbacks.items():
            if model_id not in models:
                errors.append(f"Fallback defined for non-existent model: {model_id}")

            if not isinstance(fallback_list, list):
                errors.append(f"Fallback list for {model_id} must be a list.")
            else:
                for fb_id in fallback_list:
                    if fb_id not in models:
                        errors.append(f"Fallback {model_id} -> {fb_id}: Target model does not exist in registry.")

        return len(errors) == 0, errors
