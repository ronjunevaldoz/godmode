"""
Session manager — persists multi-turn conversation history per named session.
History is stored as a list of {role, content} dicts compatible with Ollama's
/api/chat messages format.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_SESSIONS_DIR = Path(__file__).parent / "sessions"
MAX_HISTORY_CHARS = 8_000   # ~2 000 tokens — keeps context tight for 8B models


class SessionManager:
    def __init__(self, sessions_dir: Path | str = _SESSIONS_DIR) -> None:
        self.dir = Path(sessions_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.dir / f"{name}.json"

    def load(self, name: str) -> list[dict]:
        p = self._path(name)
        if not p.exists():
            return []
        try:
            return json.loads(p.read_text())
        except Exception:
            logger.warning(f"Session {name!r} corrupted — starting fresh.")
            return []

    def append(self, name: str, role: str, content: str) -> None:
        messages = self.load(name)
        messages.append({"role": role, "content": content})
        self._path(name).write_text(json.dumps(messages, indent=2))

    def truncate_to_budget(self, messages: list[dict]) -> list[dict]:
        """Return the most recent messages that fit within MAX_HISTORY_CHARS."""
        total = 0
        kept: list[dict] = []
        for msg in reversed(messages):
            cost = len(msg.get("content", ""))
            if total + cost > MAX_HISTORY_CHARS and kept:
                break
            kept.insert(0, msg)
            total += cost
        return kept

    def list_sessions(self) -> list[str]:
        return sorted(p.stem for p in self.dir.glob("*.json"))

    def clear(self, name: str) -> bool:
        p = self._path(name)
        if p.exists():
            p.unlink()
            return True
        return False

    def turn_count(self, name: str) -> int:
        return len(self.load(name)) // 2   # user + assistant pairs
