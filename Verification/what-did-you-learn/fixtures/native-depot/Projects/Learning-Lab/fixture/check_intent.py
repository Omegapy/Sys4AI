import json
from intent_router import route
cases = [
    {"name": "ambiguous", "intent": {"purpose": ""}, "expected": {"action": "clarify", "missing": ["purpose", "acceptance_criteria"]}},
    {"name": "clear", "intent": {"purpose": "Create a bounded draft", "acceptance_criteria": ["A readable draft exists"]}, "expected": {"action": "draft", "missing": []}},
]
results = [{**case, "actual": route(case["intent"]), "passed": route(case["intent"]) == case["expected"]} for case in cases]
print(json.dumps({"results": results, "passed": all(case["passed"] for case in results)}, indent=2))
raise SystemExit(0 if all(case["passed"] for case in results) else 1)
