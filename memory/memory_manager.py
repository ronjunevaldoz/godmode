import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class MemoryManager:
    """
    Handles persistence of task execution logs.
    Simple JSON-based implementation that can be swapped for SQLite/Postgres later.
    """
    def __init__(self, storage_path: str = "memory/task_logs.json"):
        self.storage_path = storage_path
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w") as f:
                json.dump([], f)

    def log_task(self, task_data: Dict[str, Any]):
        """
        Records a single routing execution.
        Expected keys: user_input, intent, target_model, confidence,
                      latency, success, fallback_used, escalation_used, notes.
        """
        task_data["timestamp"] = datetime.now().isoformat()

        logs = self._read_all()
        logs.append(task_data)
        self._write_all(logs)

    def _read_all(self) -> List[Dict[str, Any]]:
        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _write_all(self, logs: List[Dict[str, Any]]):
        with open(self.storage_path, "w") as f:
            json.dump(logs, f, indent=2)

    def get_all_logs(self) -> List[Dict[str, Any]]:
        return self._read_all()

    def query_by_model(self, model: str) -> List[Dict[str, Any]]:
        return [log for log in self._read_all() if log.get("target_model") == model]
