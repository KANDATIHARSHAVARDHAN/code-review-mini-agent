from typing import Callable, Dict

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self._tools[name] = func

    def get(self, name: str):
        return self._tools.get(name)

    def list(self):
        return list(self._tools.keys())
