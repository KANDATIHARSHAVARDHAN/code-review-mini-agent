from fastapi import FastAPI
from api.endpoints import router as api_router
from api.graph_endpoints import router as graph_router
from utils.logger import setup_logging

app = FastAPI(title="Code Review Mini-Agent")
setup_logging()
app.include_router(api_router, prefix="/api")
app.include_router(graph_router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "service": "Code Review Mini-Agent"}
