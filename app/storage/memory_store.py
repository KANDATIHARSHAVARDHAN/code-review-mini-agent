from typing import Dict, Any
from threading import RLock

class InMemoryStore:
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._graphs: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def create_run(self, run_id: str, payload: Dict[str, Any]):
        with self._lock:
            self._store[run_id] = payload

    def update_run(self, run_id: str, payload: Dict[str, Any]):
        with self._lock:
            self._store[run_id] = payload

    def get_run(self, run_id: str):
        with self._lock:
            return self._store.get(run_id)

    # graph storage helpers
    def create_graph(self, graph_id: str, payload: Dict[str, Any]):
        with self._lock:
            self._graphs[graph_id] = payload

    def get_graph(self, graph_id: str):
        with self._lock:
            return self._graphs.get(graph_id)

    def update_graph(self, graph_id: str, payload: Dict[str, Any]):
        with self._lock:
            self._graphs[graph_id] = payload

    # convenience aliases used earlier
    def create(self, key: str, val: Dict[str, Any]):
        return self.create_run(key, val)

    def get(self, key: str):
        return self.get_run(key)

    def update(self, key: str, val: Dict[str, Any]):
        return self.update_run(key, val)
