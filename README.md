# Code Review Mini-Agent (Backend)

This repository contains a backend-only implementation of a Code Review Mini-Agent (Option A) using FastAPI and a small workflow/graph engine. The goal is to analyze Python source code, extract functions, compute cyclomatic complexity, detect basic issues, suggest improvements, and iterate until a quality threshold is reached. It integrates with an LLM (Gemini) via HTTP when configured.

Run locally:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Endpoints:
- `POST /api/submit` — submit code for review. Body: `code` (string), optional `quality_threshold` (0-1).
- `GET /api/status/{run_id}` — get workflow status and results.

Environment:
- `GEMINI_API_KEY` and `GEMINI_API_URL` optionally for LLM suggestions.

Structure highlights:
- `workflows/code_review.py` — implements the analysis pipeline.
- `engine/` — tiny graph engine and node primitives.
- `storage/memory_store.py` — ephemeral in-memory run store.

Notes:
- This is intentionally small and readable; for production, replace in-memory store with persistent DB, add authentication, tests, and robust LLM error handling.
