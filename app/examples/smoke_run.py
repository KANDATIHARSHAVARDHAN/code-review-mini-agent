import json
import time
import requests

BASE = "http://127.0.0.1:8000/api"

# Load example graph
with open("examples/option_a_graph.json") as f:
    g = json.load(f)

r = requests.post(f"{BASE}/graph/create", json=g)
print("create ->", r.status_code, r.text)
graph_id = r.json()["graph_id"]

payload = {"graph_id": graph_id, "initial_state": {"code": "def foo():\n  return 1", "quality_threshold": 0.5}, "sync": True}
rr = requests.post(f"{BASE}/graph/run", json=payload)
print("run ->", rr.status_code, rr.text)

if rr.status_code == 200:
    res = rr.json()
    run_id = res.get("run_id")
    print("run_id", run_id)
    if res.get("status") == "completed":
        print("Final state:", json.dumps(res.get("state"), indent=2))
    else:
        # poll
        for _ in range(10):
            time.sleep(0.5)
            s = requests.get(f"{BASE}/graph/state/{run_id}")
            print(s.status_code, s.text)
            if s.status_code == 200 and s.json().get("status") == "completed":
                print("Finished", s.json())
                break
