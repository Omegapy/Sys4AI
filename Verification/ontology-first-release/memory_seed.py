"""Publish a clearly scoped acceptance-design note through an installed memory API."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys


def run(root, roster_file, record_id, operation):
    root = root.resolve(strict=True)
    sys.path.insert(0, str(root / ".agents/skills/memory/scripts"))
    from memory_core import json_bytes, render_record, sha256
    from memory_publish import publish, transaction_payload

    roster = json.loads(roster_file.read_text())
    assert roster["tool"] == "collaboration.list_agents"
    config = json.loads((root / "memory.yaml").read_text())
    evidence = root / "docs/frozen-input-design.md"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    if not evidence.exists():
        evidence.write_text("# Accepted fixture design\n\nThis isolated acceptance project requires a Task manager to freeze one selected ontology packet for every initial solver. Later project ontology changes must not silently enter a frozen context. This document specifies a verification fixture; it reports no historical product incident or completed native experiment.\n")
    now = datetime.now(timezone.utc)
    metadata = {
        "schema_version": 1, "id": record_id, "project_id": config["project"]["id"],
        "type": "decision", "title": "Task manager frozen input requirement", "state": "active",
        "created": now.isoformat(), "modified": now.isoformat(),
        "claim": {"level": "accepted_design", "summary": "This isolated acceptance project requires one frozen ontology packet for all initial Task manager solver assignments."},
        "applicability": ["Only this isolated ontology acceptance project."],
        "limitations": ["A fixture design input, not evidence of an earlier product failure or completed native test."],
        "confidence": "high", "sources": [{"path": "docs/frozen-input-design.md", "sha256": sha256(evidence.read_bytes()), "locator": "section:Accepted fixture design", "kind": "design"}],
        "origin": {"task_id": None, "task_path": None, "execution_id": None, "generation": None, "role": None},
        "lifecycle": {"supersedes": [], "superseded_by": None, "reason": None},
        "publication": {"actor_id": "/root", "actor_kind": "director", "operation_id": operation, "approved_at": now.isoformat()},
    }
    content = render_record({"metadata": metadata, "body": "The Task manager selects immutable ontology input before independent initial solvers launch. Reuse the same registered packet reference for queued solvers. Current Task ownership and source verification remain controlling.\n"})
    target = "MEMORY/" + record_id + ".md"
    assert not (root / target).exists(), "Do not replay an existing accepted memory operation."
    expected = {"path": target, "sha256": sha256(content), "expected_sha256": None}
    payload = transaction_payload(operation, "publish", [{"path": target, "expected_sha256": None,
                                  "content": content, "reviewed_record_sha256": expected["sha256"]}],
                                  "Publish the reviewed isolated fixture design to verify ontology-memory preservation.")
    grant = {"schema_version": 1, "grant_id": operation + "-grant", "project_id": config["project"]["id"],
             "actor_id": "/root", "actor_kind": "director", "operation": "publish",
             "payload_sha256": sha256(json_bytes(payload)), "config_sha256": sha256((root / "memory.yaml").read_bytes()),
             "scope": ["MEMORY"], "native_receipt": roster, "observed_at": now.isoformat(),
             "expires_at": (now + timedelta(minutes=5)).isoformat(), "task": None,
             "reviewed_records": [expected], "privacy_redaction": False}
    folder = root / "Verification/memory-ontology"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / (operation + "-reviewed.md")).write_text(content)
    (folder / (operation + "-payload.json")).write_bytes(json_bytes(payload))
    grant_path = folder / (operation + "-grant.json")
    grant_path.write_bytes(json_bytes(grant))
    result = publish(root, payload, grant_path.relative_to(root).as_posix(), "/root")
    (folder / (operation + "-receipt.json")).write_bytes(json_bytes(result))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--roster-file", type=Path, required=True)
    p.add_argument("--record-id", required=True)
    p.add_argument("--operation", required=True)
    a = p.parse_args()
    print(json.dumps(run(a.project_root, a.roster_file, a.record_id, a.operation), indent=2))
