

import threading
from typing import Any, Dict, Tuple
import json
import os

class SharedState:
    """Thread-safe key-value store with simple versioning."""
    def __init__(self):
        self.activated_agents = []
        self._lock = threading.RLock()
        self._version = 0
        self._state: Dict[str, Any] = {}

    def read(self, key: str, default=None):
        with self._lock:
            return self._state.get(key, default)

    def write(self, key: str, value: Any) -> int:
        with self._lock:
            self._state[key] = value
            self._version += 1
            return self._version
    
    def write_audit(self, filename: str) -> None:
        """Write the current state and version to a JSON file. Creates directories if needed."""
        with self._lock:
            data = {
                "state": self._state,
                "version": self._version
            }
            dir_path = os.path.dirname(filename)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def get_version(self) -> int:
        with self._lock:
            return self._version
