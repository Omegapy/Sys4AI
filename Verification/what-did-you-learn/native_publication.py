"""Actual owner-operated memory checks in the plan-authorized native lab."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BINDING = json.loads((HERE / "native-fixture-binding.json").read_text())
ROOT = Path(BINDING["project"])
sys.path.insert(0, str(ROOT / ".agents/skills/memory/scripts"))
from memory_core import MemoryError, health, json_bytes, load_record, load_records, render_record, sha256
from memory_capture import capture, capture_status, set_capture
from memory_publish import publish, transaction_payload
from memory_recovery import pending_transactions, recover
from memory_search import search

def write(relative, value):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else value.encode() if isinstance(value, str) else json_bytes(value))
    return relative

def ref(relative):
    return {"path": relative, "sha256": sha256((ROOT / relative).read_bytes())}

def snapshot():
    return {p.relative_to(ROOT).as_posix(): (sha256(p.read_bytes()), p.stat().st_mtime_ns)
            for p in ROOT.rglob("*") if p.is_file()}

def make_record(identifier, operation, title, summary, source, body):
    now = datetime.now(timezone.utc).isoformat()
    return {"metadata": {"schema_version": 1, "id": identifier, "project_id": "wdyl-lab", "type": "lesson", "title": title,
        "state": "active", "created": now, "modified": now, "claim": {"level": "accepted_design", "summary": summary},
        "applicability": ["The isolated Learning-Lab intent-routing fixture only; recheck current requirements before reuse."],
        "limitations": ["Controlled accepted fixture design, not production behavior or a long-term reliability measurement."],
        "confidence": "high", "sources": [{**ref(source), "locator": "document", "kind": "design"}],
        "origin": {"task_id": None, "task_path": None, "execution_id": None, "generation": None, "role": None},
        "lifecycle": {"supersedes": [], "superseded_by": None, "reason": None},
        "publication": {"actor_id": "/root", "actor_kind": "director", "operation_id": operation, "approved_at": now}}, "body": body}

def payload(record, operation="publish", previous=None, reason="Publish the exact reviewed fixture lesson under the approved native verification scope."):
    content = render_record(record)
    path = "MEMORY/" + record["metadata"]["id"] + ".md"
    return transaction_payload(record["metadata"]["publication"]["operation_id"], operation,
        [{"path": path, "expected_sha256": previous, "content": content, "reviewed_record_sha256": sha256(content)}], reason)

def prepare():
    if (ROOT / "evidence/publication/intent-payload.json").exists():
        raise SystemExit("Prepared payload exists; inspect the original operation.")
    body = """## Observation

The controlled design settles that missing purpose or acceptance criteria need clarification. The real baseline check fails the ambiguous case and passes the clear case.

## Evidence

context/intent-requirements.md defines the accepted boundary. evidence/intent-before-results.json records the actual failing check and the preserved clear fast path. The native manual review is retained separately by the Director.

## Lesson and applicability

Before drafting in this fixture, check material intent fields. Clarify the missing fields; preserve the already-clear draft path. Reassess current sources when this lesson is retrieved.

## Limitations

This is an accepted fixture design and measured baseline, not an implemented fix. It does not diagnose the production to-trd skill or establish a timeout cause.

## Improvement disposition

Targeted improvement authorized by PLAN-20260909-2AB7D4CC TASK-022: a separate later native work unit may change only fixture/intent_router.py to implement the two specified paths. Preserve all governance, memory, requirements and existing to-trd sources. This review performs no code change.

## Validation and follow-up

Later work must retrieve this canonical lesson, recheck current requirements and run fixture/check_intent.py. Publication, implementation and later observed behavior require distinct evidence. No long-term benefit has been measured.
"""
    record = make_record("MEM-20260909-A1B2C3D4", "MEMOP-wdyl-native-intent-001", "Clarify missing material intent and preserve the clear fast path",
                         "The authorized fixture design requires clarification for missing material intent while preserving the already-clear draft path.", "context/intent-requirements.md", body)
    write("evidence/publication/intent-record.json", record)
    write("evidence/publication/intent-reviewed.md", render_record(record))
    write("evidence/publication/intent-payload.json", payload(record))
    write("context/lifecycle-v1.md", "# Controlled earlier fixture design\nThe Director accepts a field-presence-only check for this lifecycle test. This is a deliberate earlier design to be revised by the conflicting evidence scenario, not the final intent implementation requirement.\n")
    body2 = """## Observation

The controlled earlier lifecycle design accepts field presence alone.

## Evidence

context/lifecycle-v1.md records this deliberately limited fixture decision.

## Lesson and applicability

For this earlier lifecycle design only, a present acceptance_criteria field satisfies presence validation.

## Limitations

This does not establish that an empty field is useful or that final intent requirements are satisfied. It is a controlled supersession input, not a production recommendation.

## Improvement disposition

Separate scoped lifecycle review must revise this note if the accepted design changes. No code change is authorized by the record itself.

## Validation and follow-up

Keep the original body and explicit history when conflicting current design supersedes this earlier decision.
"""
    second = make_record("MEM-20260909-B2C3D4E5", "MEMOP-wdyl-native-explicit-001", "Earlier controlled field-presence rule",
                         "The Director accepted a deliberately limited field-presence rule for the isolated lifecycle test.", "context/lifecycle-v1.md", body2)
    write("evidence/publication/explicit-record.json", second)
    write("evidence/publication/explicit-reviewed.md", render_record(second))
    write("evidence/publication/explicit-payload.json", payload(second))
    print(json.dumps({"reviewed": [ref("evidence/publication/intent-reviewed.md"), ref("evidence/publication/explicit-reviewed.md")]}))

def grant(payload_value, name, operation=None):
    observation = json.loads((HERE / "native-publication-roster.json").read_text())
    observed = datetime.fromisoformat(observation["observed_at"])
    grant_value = {"schema_version": 1, "grant_id": name, "project_id": "wdyl-lab", "actor_id": "/root", "actor_kind": "director",
        "operation": operation or payload_value["operation"], "payload_sha256": sha256(json_bytes(payload_value)),
        "config_sha256": ref("memory.yaml")["sha256"], "scope": ["MEMORY"], "native_receipt": observation["receipt"],
        "observed_at": observed.isoformat(), "expires_at": (observed + timedelta(minutes=5)).isoformat(), "task": None,
        "reviewed_records": [{"path": c["path"], "sha256": c["reviewed_record_sha256"], "expected_sha256": c["expected_sha256"]} for c in payload_value["changes"]],
        "privacy_redaction": False}
    return write("evidence/publication/" + name + "-grant.json", grant_value)

def first_publications():
    p = json.loads((ROOT / "evidence/publication/intent-payload.json").read_text())
    g = grant(p, "intent-owner")
    first = capture(ROOT, p, g, "/root", trigger="decision-recorded")
    canonical = load_record(ROOT, p["changes"][0]["path"])
    assert canonical["sha256"] == p["changes"][0]["reviewed_record_sha256"]
    before = snapshot()
    retry = capture(ROOT, p, g, "/root", trigger="decision-recorded")
    assert first == retry and snapshot() == before
    hits = search(ROOT, "Clarify missing material intent", mode="lexical")
    assert any(x.get("record_id") == "MEM-20260909-A1B2C3D4" for x in hits["results"])
    original_config = (ROOT / "memory.yaml").read_bytes()
    preference = set_capture(ROOT, False, capture_status(ROOT)["config_sha256"])
    before = snapshot()
    automatic = capture(ROOT, {}, "absent-grant.json", "/root", trigger="work-completed")
    assert automatic["reason"] == "automatic_capture_off" and snapshot() == before
    p2 = json.loads((ROOT / "evidence/publication/explicit-payload.json").read_text())
    g2 = grant(p2, "explicit-owner")
    before = snapshot()
    try:
        publish(ROOT, p2, g2, "/root/native_review")
        raise AssertionError("Child actor was unexpectedly allowed to publish")
    except MemoryError as error:
        unauthorized = {"code": error.code, "message": str(error), "details": error.details, "optional_capture": "reported without failing accepted work", "required_publication": "unmet before owner publication"}
    assert snapshot() == before
    off_config = (ROOT / "memory.yaml").read_bytes()
    explicit = publish(ROOT, p2, g2, "/root")
    assert (ROOT / "memory.yaml").read_bytes() == off_config
    restore = set_capture(ROOT, True, capture_status(ROOT)["config_sha256"])
    result = {"status": "passed", "first_capture": first, "canonical": {"path": canonical["path"], "sha256": canonical["sha256"], "diagnostics": canonical["diagnostics"]},
              "retry_same_receipt_and_full_snapshot": True, "lexical": hits, "capture_off": automatic, "preference_change": preference,
              "unauthorized": unauthorized, "explicit_save_while_off": explicit, "restore": restore, "original_config_restored_exactly": (ROOT / "memory.yaml").read_bytes() == original_config,
              "health": health(ROOT), "active_record_count": len(load_records(ROOT))}
    (HERE / "native-first-publications.json").write_bytes(json_bytes(result))
    print(json.dumps({"status": "passed", "active_records": len(load_records(ROOT)), "unauthorized": unauthorized["code"], "backend": result["health"]["backend"]}))

def prepare_supersession():
    write("context/lifecycle-v2.md", "# Controlled revised fixture design\nThe Director now accepts that acceptance criteria must be non-empty. A present but empty field is missing material intent. This supersedes the deliberate field-presence-only lifecycle test design in context/lifecycle-v1.md; retain its history.\n")
    old = load_record(ROOT, "MEMORY/MEM-20260909-B2C3D4E5.md")
    previous = {"metadata": deepcopy(old["metadata"]), "body": old["body"]}
    reason = "Current controlled design requires non-empty acceptance criteria; preserve the earlier limited decision as superseded history."
    body = """## Observation

The current controlled lifecycle design rejects a present but empty acceptance-criteria field.

## Evidence

context/lifecycle-v2.md records the revised accepted fixture design and identifies its predecessor.

## Lesson and applicability

Recheck content, not only field presence, when deciding whether this fixture's material intent is complete.

## Limitations

This is a controlled lifecycle revision. The later implementation unit must independently recheck current intent requirements and behavior.

## Improvement disposition

The original field-presence-only note is superseded while its original body and history remain. Any code improvement remains restricted to the separately authorized fixture target.

## Validation and follow-up

The actual two-record supersession must recover the original operation after a controlled interruption. Verify one active successor and one retained superseded predecessor before reporting success.
"""
    successor = make_record("MEM-20260909-C3D4E5F6", "MEMOP-wdyl-native-supersede-001", "Validate material field content against current requirements",
                            "The revised controlled design requires non-empty acceptance criteria, superseding the earlier presence-only rule.", "context/lifecycle-v2.md", body)
    successor["metadata"]["lifecycle"] = {"supersedes": [previous["metadata"]["id"]], "superseded_by": None, "reason": reason}
    previous["metadata"]["state"] = "superseded"
    previous["metadata"]["modified"] = successor["metadata"]["modified"]
    previous["metadata"]["publication"] = deepcopy(successor["metadata"]["publication"])
    previous["metadata"]["lifecycle"] = {"supersedes": [], "superseded_by": successor["metadata"]["id"], "reason": reason}
    changes = []
    for label, rec, prior in (("successor", successor, None), ("predecessor", previous, old["sha256"])):
        raw = render_record(rec)
        write("evidence/publication/" + label + "-reviewed.md", raw)
        changes.append({"path": "MEMORY/" + rec["metadata"]["id"] + ".md", "expected_sha256": prior, "content": raw, "reviewed_record_sha256": sha256(raw)})
    write("evidence/publication/supersede-payload.json", transaction_payload(successor["metadata"]["publication"]["operation_id"], "supersede", changes, reason))
    print(json.dumps({"reviewed": [ref("evidence/publication/" + x + "-reviewed.md") for x in ("successor", "predecessor")]}))

def supersession():
    p = json.loads((ROOT / "evidence/publication/supersede-payload.json").read_text())
    g = grant(p, "supersede-owner")
    def interrupt(boundary):
        if boundary == "after_record_0":
            raise OSError("Controlled native-lab interruption after actual successor replacement")
    try:
        publish(ROOT, p, g, "/root", fault=interrupt)
        raise AssertionError("Expected the controlled partial operation")
    except MemoryError as error:
        assert error.code == "publication_interrupted", (error.code, str(error))
        partial = {"code": error.code, "message": str(error), "details": error.details, "required_publication": "unmet until exact recovery"}
    pending = pending_transactions(ROOT)
    assert len(pending) == 1, pending
    journal_path = pending[0]["journal_path"] if "journal_path" in pending[0] else pending[0]["path"]
    journal_before = json.loads((ROOT / journal_path).read_text())
    blocked = None
    try:
        load_records(ROOT)
    except MemoryError as error:
        blocked = error.code
    assert blocked
    g2 = grant(p, "recover-owner", "recover")
    result = recover(ROOT, journal_path, g2, "/root")
    assert result["state"] == "complete" and not result["task_events_replayed"]
    old = load_record(ROOT, "MEMORY/MEM-20260909-B2C3D4E5.md")
    new = load_record(ROOT, "MEMORY/MEM-20260909-C3D4E5F6.md")
    original = json.loads((ROOT / "evidence/publication/explicit-record.json").read_text())
    assert old["body"] == original["body"] and old["metadata"]["state"] == "superseded"
    assert new["metadata"]["lifecycle"]["supersedes"] == [old["metadata"]["id"]]
    report = {"status": "passed", "partial": partial, "journal_before": journal_before, "blocked_retrieval": blocked, "recovery": result,
              "journal_after": json.loads((ROOT / journal_path).read_text()), "original_body_preserved": True,
              "active_record_ids": [r["metadata"]["id"] for r in load_records(ROOT)], "predecessor": ref(old["path"]), "successor": ref(new["path"])}
    (HERE / "native-supersession-results.json").write_bytes(json_bytes(report))
    print(json.dumps({"status": "passed", "active_record_ids": report["active_record_ids"], "partial_code": partial["code"], "retrieval_during_partial": blocked}))

if __name__ == "__main__":
    {"prepare": prepare, "first": first_publications, "prepare-supersession": prepare_supersession, "supersede": supersession}[sys.argv[1]]()
