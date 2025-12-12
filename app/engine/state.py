from typing import Dict, Any

class StateManager:
    def __init__(self):
        self._state: Dict[str, Any] = {}

    def get(self, key: str, default=None):
        return self._state.get(key, default)

    def set(self, key: str, value: Any):
        self._state[key] = value

    def update(self, mapping: Dict[str, Any]):
        self._state.update(mapping)

    def as_dict(self):
        return dict(self._state)
