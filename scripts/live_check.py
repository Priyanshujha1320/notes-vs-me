"""Live end-to-end check against the running server + local model."""
import json
import sys
import urllib.request

BASE = "http://localhost:8000"


def call(path, payload=None, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method or ("POST" if data else "GET"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


qs = call("/api/quiz/next?count=3", {})
print(f"generated {len(qs)} questions:")
for q in qs:
    print(f"  #{q['id']} [{q['topic']}] ({q['type']}) {q['question'][:90]}")

# answer the first mcq (or any) correctly/incorrectly to exercise grading
q0 = qs[0]
if q0["type"] == "mcq":
    ans = q0["options"][0]
else:
    ans = "I think it happens in the stroma and uses ATP."
res = call(f"/api/answer/{q0['id']}", {"answer": ans})
print("graded:", res)
print("stats:", json.dumps(call("/api/stats"), indent=1)[:400])
