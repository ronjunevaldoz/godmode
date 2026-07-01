import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent


class CapabilityResolver:
    """Maps a detected intent to the set of capabilities required to fulfill it."""

    def __init__(self, map_path: str | Path = ROOT / "routing" / "intent_map.json") -> None:
        self.map_path = Path(map_path)
        self._intent_map: dict[str, list[str]] = self._load_map()

    def _load_map(self) -> dict[str, list[str]]:
        try:
            with open(self.map_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading intent map: {e}")
            return {}

    def resolve_capabilities(self, intent: str) -> list[str]:
        """Returns required capabilities for an intent; falls back to UNKNOWN defaults."""
        return self._intent_map.get(intent, self._intent_map.get("UNKNOWN", ["long_context_reasoning"]))
