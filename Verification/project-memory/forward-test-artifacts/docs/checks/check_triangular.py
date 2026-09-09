import json
cases = [1, 10, 100]
results = []
for n in cases:
    direct = sum(range(1, n + 1))
    closed = n * (n + 1) // 2
    assert direct == closed, (n, direct, closed)
    results.append({"n": n, "direct_sum": direct, "closed_form": closed})
print(json.dumps({"outcome": "passed", "cases": results}))
