from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from uuid import uuid4
from ..storage.memory_store import InMemoryStore
from ..engine.graph import GraphEngine
from ..engine.node import Node
from ..engine.registry import ToolRegistry
from ..workflows import code_review
from .models import GraphCreate, GraphRunRequest, GraphRunResponse

router = APIRouter()
store = InMemoryStore()
engine = GraphEngine()
registry = ToolRegistry()

# pre-register some useful tools (functions) from the code_review workflow
registry.register("extract_functions", code_review.extract_functions)
registry.register("cyclomatic_complexity", code_review.cyclomatic_complexity)
registry.register("detect_basic_issues", code_review.detect_basic_issues)
registry.register("suggest_improvements", code_review.suggest_improvements)
# register scoring + predicate tools
registry.register("compute_quality", code_review.compute_quality_score)
registry.register("quality_below_threshold", code_review.quality_below_threshold)


@router.post("/graph/create")
def create_graph(payload: GraphCreate):
    """Create a graph from a simple JSON description.

    Expected payload example:
    {
      "nodes": [{"id": "extract", "tool": "extract_functions"}, ...],
      "edges": [{"from": "extract", "to": "analyze", "cond": null}, ...],
      "start": "extract"
    }
    """
    graph_id = str(uuid4())
    # store the validated dict representation
    store.create_graph(graph_id, payload.dict(by_alias=True))
    return {"graph_id": graph_id}


@router.post("/graph/run")
def run_graph(payload: GraphRunRequest, background_tasks: BackgroundTasks):
    """Run a stored graph. Payload: {"graph_id": str, "initial_state": {...}, "max_iterations": 10}
    If background_tasks is provided by FastAPI, the run will be scheduled in background and an immediate
    run_id will be returned. Otherwise the run is executed synchronously and final state is returned.
    """
    graph_id = payload.get("graph_id")
    if not graph_id:
        raise HTTPException(status_code=400, detail="graph_id required")
    graph_def = store.get_graph(graph_id)
    if not graph_def:
        raise HTTPException(status_code=404, detail="graph not found")

    # build engine instance from graph_def; provide registry for predicates
    local_engine = GraphEngine(predicate_registry=registry)
    nodes = graph_def.get("nodes", [])
    for n in nodes:
        nid = n.get("id")
        tool = n.get("tool")
        if not nid or not tool:
            continue
        func = registry.get(tool)
        if not func:
            # allow inline Python? For security, we reject unknown tools
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool}")
        local_engine.add_node(Node(nid, func))

    for e in graph_def.get("edges", []):
        frm = e.get("from")
        to = e.get("to")
        cond = e.get("cond")
        local_engine.add_edge(frm, to, condition=cond)

    start = graph_def.get("start")
    if not start:
        raise HTTPException(status_code=400, detail="graph missing start node")

    initial_state = payload.initial_state or {}
    max_iters = payload.max_iterations or 10
    sync = payload.sync

    run_id = str(uuid4())
    store.create_run(run_id, {"status": "pending", "state": initial_state, "log": []})

    def _run_and_store(rid: str):
        try:
            res = local_engine.run(start, initial_state, max_iterations=max_iters)
            store.update_run(rid, {"status": "completed", "state": res.get("state"), "log": res.get("log"), "iterations": res.get("iterations")})
        except Exception as exc:
            store.update_run(rid, {"status": "failed", "error": str(exc)})

    # schedule or run synchronously based on request
    if sync:
        _run_and_store(run_id)
        entry = store.get_run(run_id)
        return GraphRunResponse(run_id=run_id, status=entry.get("status"), state=entry.get("state"), log=entry.get("log"), iterations=entry.get("iterations"))

    background_tasks.add_task(_run_and_store, run_id)
    return GraphRunResponse(run_id=run_id, status="scheduled")


@router.get("/graph/state/{run_id}")
def graph_state(run_id: str):
    entry = store.get_run(run_id)
    if not entry:
        raise HTTPException(status_code=404, detail="run not found")
    return entry