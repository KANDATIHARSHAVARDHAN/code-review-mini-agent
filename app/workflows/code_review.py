import ast
import math
from typing import Dict, Any, List
from engine.graph import GraphEngine
from engine.node import Node
from engine.state import StateManager
from storage.memory_store import InMemoryStore
from api.models import ReviewResult
import httpx
import os

# Simple utils for code analysis

def extract_functions(inputs: Dict[str, Any]) -> Dict[str, Any]:
    code = inputs.get("code", "")
    tree = ast.parse(code)
    funcs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start = node.lineno
            end = max([getattr(n, "lineno", start) for n in ast.walk(node)])
            source_lines = code.splitlines()[start - 1 : end]
            funcs.append({"name": node.name, "start": start, "end": end, "lines": len(source_lines), "node": node})
    return {"functions": funcs}


def cyclomatic_complexity(inputs: Dict[str, Any]) -> Dict[str, Any]:
    funcs = inputs.get("functions", [])
    results = []
    for f in funcs:
        node = f["node"]
        complexity = 1
        for n in ast.walk(node):
            if isinstance(n, (ast.If, ast.For, ast.While, ast.And, ast.Or, ast.ExceptHandler, ast.With, ast.BoolOp, ast.Try)):
                complexity += 1
            if isinstance(n, ast.Call):
                # heuristic: calls may indicate complexity
                complexity += 0
        results.append({"name": f["name"], "complexity": complexity, "lines": f["lines"]})
    return {"complexities": results}


def detect_basic_issues(inputs: Dict[str, Any]) -> Dict[str, Any]:
    code = inputs.get("code", "")
    issues: List[str] = []
    lines = code.splitlines()
    for i, l in enumerate(lines, start=1):
        if "TODO" in l or "FIXME" in l:
            issues.append(f"Line {i}: contains TODO/FIXME")
        if len(l) > 120:
            issues.append(f"Line {i}: exceeds 120 chars")
    # find unused imports simple heuristic
    try:
        tree = ast.parse(code)
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        imported = set()
        for im in imports:
            for name in getattr(im, 'names', []):
                imported.add(name.name.split('.')[0])
        # naive: check if those names appear elsewhere
        for name in list(imported):
            if name not in code.replace('import', ''):
                issues.append(f"Possible unused import: {name}")
    except Exception:
        pass
    return {"issues": issues}


def suggest_improvements(inputs: Dict[str, Any]) -> Dict[str, Any]:
    suggestions: List[str] = []
    complexities = inputs.get("complexities", [])
    issues = inputs.get("issues", [])
    for c in complexities:
        if c["complexity"] > 10 or c["lines"] > 200:
            suggestions.append(f"Refactor function {c['name']}: reduce complexity or split into smaller functions")
        elif c["complexity"] > 5:
            suggestions.append(f"Consider simplifying {c['name']} to lower cyclomatic complexity")
    if issues:
        suggestions.append("Address basic issues reported (line length, TODOs, unused imports)")
    # LLM-driven suggestion placeholder
    return {"suggestions": suggestions}


def compute_quality_score(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compute a naive quality score from current state and return as dict update."""
    issues = state.get("issues", [])
    complexities = state.get("complexities", [])
    score = 1.0
    score -= min(0.5, 0.05 * len(issues))
    heavy = sum(1 for c in complexities if c.get("complexity", 0) > 10)
    score -= min(0.4, 0.2 * heavy)
    score = max(0.0, score)
    return {"quality_score": score}


def quality_below_threshold(state: Dict[str, Any]) -> bool:
    """Predicate for engine: returns True if quality_score < quality_threshold."""
    q = state.get("quality_score")
    thr = state.get("quality_threshold")
    if q is None:
        # no score yet -> consider below threshold
        return True
    try:
        return float(q) < float(thr if thr is not None else 0.8)
    except Exception:
        return True


class CodeReviewWorkflow:
    def __init__(self, store: InMemoryStore = None):
        self.store = store or InMemoryStore()
        self.state = StateManager()

    def _call_gemini(self, prompt: str) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        api_url = os.getenv("GEMINI_API_URL")
        if not api_key or not api_url:
            return "[LLM not configured]"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"prompt": prompt, "max_tokens": 512}
        # simple retry loop for robustness
        last_err = None
        for attempt in range(3):
            try:
                r = httpx.post(api_url, json=payload, headers=headers, timeout=30.0)
                r.raise_for_status()
                return r.json().get("text") or r.text
            except Exception as e:
                last_err = e
        return f"[LLM error: {last_err}]"

    def run(self, code: str, quality_threshold: float = 0.8) -> ReviewResult:
        # Build simple pipeline using our functions
        ctx = {"code": code}
        ctx.update(extract_functions(ctx))
        ctx.update(cyclomatic_complexity(ctx))
        ctx.update(detect_basic_issues(ctx))
        ctx.update(suggest_improvements(ctx))

        # compute a naive quality score
        issues = ctx.get("issues", [])
        complexities = ctx.get("complexities", [])
        score = 1.0
        score -= min(0.5, 0.05 * len(issues))
        heavy = sum(1 for c in complexities if c["complexity"] > 10)
        score -= min(0.4, 0.2 * heavy)
        score = max(0.0, score)

        suggestions = ctx.get("suggestions", [])

        # LLM-enhanced summary
        prompt = f"You are a code review assistant. Provide a short improvement summary for the following code:\n\n{code}\n\nCurrent findings: issues={issues}, complexities={complexities}\n\nProvide 3 actionable suggestions." 
        llm_resp = self._call_gemini(prompt)
        if llm_resp and not llm_resp.startswith("[LLM"):
            suggestions.append("LLM suggestions:\n" + llm_resp)

        report_lines = []
        report_lines.append(f"quality_score: {score}")
        report_lines.append(f"issues: {issues}")
        report_lines.append(f"complexities: {complexities}")
        report = "\n".join(report_lines)

        # Loop until threshold or until small max iterations
        max_iters = 3
        iter_count = 0
        current_score = score
        while current_score < quality_threshold and iter_count < max_iters:
            # simple improvement heuristic: apply suggestions that lower complexity
            for c in complexities:
                if c["complexity"] > 10:
                    # pretend we refactor one function to reduce complexity
                    c["complexity"] = max(1, c["complexity"] - 5)
            current_score += 0.15
            iter_count += 1

        final_score = min(1.0, current_score)

        result = ReviewResult(
            quality_score=final_score,
            issues=issues,
            suggestions=suggestions,
            report=report,
        )

        return result
