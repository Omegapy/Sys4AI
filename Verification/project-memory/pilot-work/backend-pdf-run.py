"""Normalize a real PDF in root extraction runtime, query in the pilot runtime."""
import importlib.util
import json
from pathlib import Path
import time

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pilot", BASE / "backend-fixture-run.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
import fitz
from memory_search import collect_documents, search
from memory_maintenance import reindex_payload, reindex
from basic_memory_adapter import query

root = pilot.fixture("pdf-source")
runtime_link = root / ".venv-memory-pilot"
if not runtime_link.exists():
    runtime_link.symlink_to(pilot.DEPOT / ".venv-memory-pilot", target_is_directory=True)
pdf_path = root / "research/thermal.pdf"
if not pdf_path.exists():
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "PDF-THERMAL-914: Passive radiators reject satellite waste heat into space.")
    document.save(pdf_path)
    document.close()
before = pilot.snapshot(root, True)
payload = reindex_payload(root)
rel, sha = pilot.grant(root, payload, "pdf-reindex-" + str(time.time_ns()))
result = {"schema_version": 1, "level": "actual-vendor-with-actual-pdf-extraction", "extractor_version": fitz.VersionBind,
          "runtime_link": {"path": str(runtime_link), "target": str(runtime_link.resolve()), "scope": "explicit shared pilot executable only; excluded from source corpus"}}
try:
    result["reindex"] = reindex(root, grant_file=rel, actor=pilot.ACTOR, expected_payload_sha256=sha)
    result["canonical_preserved"] = before == pilot.snapshot(root, True)
    reading = pilot.snapshot(root)
    result["exact"] = query(root, "PDF-THERMAL-914", mode="text")
    result["hybrid"] = search(root, "PDF-THERMAL-914", mode="hybrid")
    result["reads_preserved"] = reading == pilot.snapshot(root)
except Exception as exc:
    result["error"] = {"code": getattr(exc, "code", type(exc).__name__), "message": str(exc), "details": getattr(exc, "details", {})}
(BASE.parent / "backend-pdf-results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k not in {"exact", "hybrid", "reindex"}}, indent=2))
