from typing import Any
from storage.memory_store import InMemoryStore

class BaseWorkflow:
    def __init__(self, store: InMemoryStore):
        self.store = store

    def run(self, *args, **kwargs) -> Any:
        raise NotImplementedError()
