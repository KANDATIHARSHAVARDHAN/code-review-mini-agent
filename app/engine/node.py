from typing import Any, Callable, Dict

class Node:
    def __init__(self, id: str, func: Callable[..., Any], meta: Dict = None):
        self.id = id
        self.func = func
        self.meta = meta or {}

    def run(self, inputs: Dict[str, Any]) -> Any:
        return self.func(inputs)
