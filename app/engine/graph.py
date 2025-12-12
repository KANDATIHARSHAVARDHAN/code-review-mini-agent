from typing import Dict, List, Any, Callable, Optional
from .node import Node
from .state import StateManager


class GraphEngine:
    """A minimal graph engine with support for conditional edges and a simple loop mechanism.

    Edges are stored as a mapping:
      edges[from_node] = [ {"to": to_node_id, "cond": "state['x'] > 0"}, ... ]

    Conditions are optional strings evaluated with `state` available. This is simple
    and intended for demo/assignment use only (do not eval untrusted code in production).
    """

    def __init__(self, predicate_registry: Optional[Callable] = None):
        self.nodes: Dict[str, Node] = {}
        # edges[from] -> list of dicts {"to": str, "cond": Optional[str]}
        self.edges: Dict[str, List[Dict[str, Optional[str]]]] = {}
        # predicate_registry should provide .get(name) -> callable(state)->bool
        self.predicate_registry = predicate_registry

    def add_node(self, node: Node):
        self.nodes[node.id] = node
        self.edges.setdefault(node.id, [])

    def add_edge(self, from_id: str, to_id: str, condition: Optional[str] = None):
        self.edges.setdefault(from_id, []).append({"to": to_id, "cond": condition})

    def run(self, start_node_id: str, initial_state: Dict[str, Any], max_iterations: int = 10) -> Dict[str, Any]:
        """Run the graph starting at `start_node_id`.

        - `initial_state` is a dict that will be wrapped in a `StateManager`.
        - `max_iterations` prevents infinite loops.
        Returns the final state dict.
        """
        state = StateManager()
        state.update(initial_state)

        # simple work queue: (node_id)
        queue: List[str] = [start_node_id]
        log: List[Dict[str, Any]] = []
        iterations = 0

        while queue and iterations < max_iterations:
            iterations += 1
            nid = queue.pop(0)
            node = self.nodes.get(nid)
            if node is None:
                log.append({"node": nid, "status": "missing"})
                continue

            try:
                out = node.run(state.as_dict())
                if isinstance(out, dict):
                    state.update(out)
                log.append({"node": nid, "status": "ok", "output": out})
            except Exception as e:
                log.append({"node": nid, "status": "error", "error": str(e)})

            # enqueue children according to their conditions
            for edge in self.edges.get(nid, []):
                target = edge.get("to")
                cond = edge.get("cond")
                take = True
                if cond:
                    # cond is expected to be the name of a registered predicate
                    take = False
                    if self.predicate_registry:
                        pred = self.predicate_registry.get(cond)
                        if pred:
                            try:
                                take = bool(pred(state.as_dict()))
                            except Exception:
                                take = False
                if take:
                    queue.append(target)

        # final return: include state and a short log
        return {"state": state.as_dict(), "log": log, "iterations": iterations}
