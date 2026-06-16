import json
from typing import List, Dict

class CapabilityResolver:
    """
    Maps a detected intent to the set of capabilities required to fulfill it.
    """
    def __init__(self, map_path: str = "routing/intent_map.json"):
        self.map_path = map_path
        self._intent_map = self._load_map()

    def _load_map(self) -> Dict[str, List[str]]:
        try:
            with open(self.map_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading intent map: {e}")
            return {}

    def resolve_capabilities(self, intent: str) -> List[str]:
        """
        Returns the list of required capabilities for a given intent.
        Falls back to 'UNKNOWN' requirements if intent is not found.
        """
        return self._intent_map.get(intent, self._intent_map.get("UNKNOWN", ["long_context_reasoning"]))
