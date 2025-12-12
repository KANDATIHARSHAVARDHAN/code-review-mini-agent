from pydantic import BaseModel, Field
from typing import Optional, List

class SubmitCodeRequest(BaseModel):
    repo_name: Optional[str] = Field(None, description="Optional repo name")
    file_path: Optional[str] = Field(None, description="Optional file path in repo")
    code: str = Field(..., description="Source code to analyze")
    quality_threshold: float = Field(0.8, description="Target quality score between 0 and 1")

class ReviewResult(BaseModel):
    quality_score: float
    issues: List[str]
    suggestions: List[str]
    report: Optional[str]

class WorkflowStatus(BaseModel):
    id: str
    status: str
    result: Optional[ReviewResult]


# Graph schemas for /api/graph/create
class NodeSchema(BaseModel):
    id: str
    tool: str


class EdgeSchema(BaseModel):
    from_node: str = Field(..., alias="from")
    to: str
    cond: Optional[str] = None


class GraphCreate(BaseModel):
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]
    start: str

    class Config:
        allow_population_by_field_name = True


class GraphRunRequest(BaseModel):
    graph_id: str
    initial_state: Optional[Dict[str, Any]] = Field(default_factory=dict)
    max_iterations: Optional[int] = 10
    sync: Optional[bool] = False


class GraphRunResponse(BaseModel):
    run_id: str
    status: str
    state: Optional[Dict[str, Any]] = None
    log: Optional[List[Dict[str, Any]]] = None
    iterations: Optional[int] = None
