"""Actual SQLAlchemy/vendor regression for literal URI characters in root paths."""
import importlib.util
import json
from pathlib import Path
import time

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pilot", BASE / "backend-fixture-run.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
from basic_memory_adapter import query
from memory_maintenance import reindex_payload, reindex
from memory_core import load_config

root = BASE / "fixtures/url? literal #"
if not root.exists():
    pilot.fixture("url-literal").rename(root)
config = load_config(root)
before = pilot.snapshot(root, True)
payload = reindex_payload(root)
rel, sha = pilot.grant(root, payload, "literal-url-" + str(time.time_ns()))
outside_prefix = root.parent / "url"
assert not outside_prefix.exists()
result = {"schema_version": 1, "level": "actual-vendor-special-character-project-path", "project_root": str(root)}
try:
    result["reindex"] = reindex(root, grant_file=rel, actor=pilot.ACTOR, expected_payload_sha256=sha)
    result["canonical_preserved"] = before == pilot.snapshot(root, True)
    read_before = pilot.snapshot(root)
    result["query"] = query(root, "passive satellite cooling")
    result["reads_preserved"] = read_before == pilot.snapshot(root)
    result["declared_database_exists"] = (root / config["state"]["index"] / "basic-memory.db").is_file()
    result["truncated_outside_path_absent"] = not outside_prefix.exists()
except Exception as exc:
    result["error"] = {"code": getattr(exc, "code", type(exc).__name__), "message": str(exc), "details": getattr(exc, "details", {})}
(BASE.parent / "backend-url-results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k not in {"query", "reindex"}}, indent=2))
