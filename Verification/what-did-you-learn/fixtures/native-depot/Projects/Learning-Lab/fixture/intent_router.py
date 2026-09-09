def route(intent):
    missing = [field for field in ("purpose", "acceptance_criteria") if not intent.get(field)]
    if missing:
        return {"action": "clarify", "missing": missing}
    return {"action": "draft", "missing": []}
