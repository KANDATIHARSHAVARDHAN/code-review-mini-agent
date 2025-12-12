from fastapi import APIRouter, BackgroundTasks, HTTPException
from uuid import uuid4
from api.models import SubmitCodeRequest, WorkflowStatus, ReviewResult
from workflows.code_review import CodeReviewWorkflow
from storage.memory_store import InMemoryStore

router = APIRouter()
store = InMemoryStore()


@router.post("/submit", response_model=WorkflowStatus)
def submit_code(request: SubmitCodeRequest, background_tasks: BackgroundTasks):
    workflow = CodeReviewWorkflow(store=store)
    run_id = str(uuid4())
    store.create_run(run_id, {"status": "pending", "result": None})
    background_tasks.add_task(_run_workflow, run_id, request)
    return WorkflowStatus(id=run_id, status="pending", result=None)


def _run_workflow(run_id: str, request: SubmitCodeRequest):
    workflow = CodeReviewWorkflow(store=store)
    try:
        result = workflow.run(request.code, request.quality_threshold)
        store.update_run(run_id, {"status": "completed", "result": result.dict()})
    except Exception as e:
        store.update_run(run_id, {"status": "failed", "result": {"error": str(e)}})


@router.get("/status/{run_id}", response_model=WorkflowStatus)
def get_status(run_id: str):
    entry = store.get_run(run_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Run not found")
    result = entry.get("result")
    if result and isinstance(result, dict):
        try:
            rr = ReviewResult(**result)
        except Exception:
            rr = None
    else:
        rr = None
    return WorkflowStatus(id=run_id, status=entry.get("status"), result=rr)
