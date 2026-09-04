import urllib.request, json

def get(url):
    try:
        req = urllib.request.urlopen(url, timeout=10)
        return json.loads(req.read())
    except Exception as e:
        return {"error": str(e)}

def post(url, data):
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

BASE = "http://localhost:8000"

print("=== API Root ===")
print(json.dumps(get(BASE + "/"), indent=2))

print("\n=== API Endpoints ===")
spec = get(BASE + "/openapi.json")
if "paths" in spec:
    for path in sorted(spec["paths"].keys()):
        methods = list(spec["paths"][path].keys())
        print("  " + path + " [" + ", ".join(methods) + "]")

print("\n=== Scenarios ===")
data = get(BASE + "/api/v1/scenarios")
if isinstance(data, list):
    print("Total: " + str(len(data)))
    for s in data[:5]:
        print("  - " + str(s.get("scenario_id")) + ": " + str(s.get("name")))
else:
    print(json.dumps(data, indent=2))

print("\n=== Release Gate ===")
print(json.dumps(get(BASE + "/api/v1/release-gate"), indent=2))

print("\n=== Benchmarks Latest ===")
print(json.dumps(get(BASE + "/api/v1/benchmarks/latest"), indent=2))

print("\n=== Recent Runs ===")
runs = get(BASE + "/api/v1/runs?limit=5")
if isinstance(runs, list):
    print("Total: " + str(len(runs)))
    for r in runs:
        print("  - " + str(r.get("run_id")) + " agent=" + str(r.get("agent_type")) + " status=" + str(r.get("status")))
else:
    print(json.dumps(runs, indent=2))

print("\n=== Execute Guarded Run (sc_001) ===")
run_result = post(BASE + "/api/v1/runs", {"scenario_id": "sc_001", "agent_type": "guarded", "user_role": "customer", "user_id": "user_001"})
print(json.dumps(run_result, indent=2))

if "run_id" in run_result:
    rid = run_result["run_id"]
    print("\n=== Trace for Run " + rid + " ===")
    trace = get(BASE + "/api/v1/runs/" + rid + "/trace")
    if isinstance(trace, list):
        print("Total steps: " + str(len(trace)))
        for step in trace[:5]:
            print("  - node=" + str(step.get("node")) + " action=" + str(step.get("action")))
    else:
        print(json.dumps(trace, indent=2))

print("\n=== Approvals Inbox ===")
approvals = get(BASE + "/api/v1/approvals")
if isinstance(approvals, list):
    print("Pending: " + str(len(approvals)))
    for a in approvals[:3]:
        print("  - id=" + str(a.get("id")) + " action=" + str(a.get("action")))
else:
    print(json.dumps(approvals, indent=2))

print("\n=== Evidence Ledger (last 3) ===")
evidence = get(BASE + "/api/v1/evidence?limit=3")
print(json.dumps(evidence, indent=2))

print("\n=== Ledger Integrity Verify ===")
verify = get(BASE + "/api/v1/evidence/verify")
print(json.dumps(verify, indent=2))

print("\nDONE")
