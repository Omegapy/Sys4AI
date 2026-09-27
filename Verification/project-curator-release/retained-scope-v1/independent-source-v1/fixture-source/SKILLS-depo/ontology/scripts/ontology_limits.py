"""Finite advanced budgets. Call overrides can only lower project limits."""
from ontology_core import require

DEFAULTS = {"input_bytes": 8 * 1024 * 1024, "input_triples": 50000,
            "query_seconds": 10, "result_rows": 500, "output_bytes": 1024 * 1024,
            "reasoning_seconds": 30, "derived_triples": 100000, "rule_rounds": 128,
            "proof_nodes": 10000, "workers": 2, "rss_bytes": 512 * 1024 * 1024,
            "guard_seconds": 5, "query_depth": 64}
# These are release ceilings, rather than promises that a host can meet them.
CEILINGS = {**DEFAULTS, "input_bytes": 32 * 1024 * 1024, "input_triples": 200000,
            "query_seconds": 60, "result_rows": 5000, "output_bytes": 8 * 1024 * 1024,
            "reasoning_seconds": 120, "derived_triples": 400000, "rule_rounds": 512,
            "proof_nodes": 40000, "rss_bytes": 1024 * 1024 * 1024}


def limits(config=None, overrides=None):
    values = dict(DEFAULTS)
    for selected, ceilings in ((config or {}, CEILINGS), (overrides or {}, None)):
        require(isinstance(selected, dict) and set(selected) <= set(DEFAULTS), "invalid_limits", "Unknown advanced budget.")
        for key, value in selected.items():
            require(type(value) is int and 1 <= value <= (ceilings or values)[key], "invalid_limits", "Budget must be a positive integer within its current ceiling: " + key)
        values.update(selected)
    return values
