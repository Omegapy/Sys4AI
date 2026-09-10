"""Actual reciprocal publication and stale-link checks in the isolated v7 project."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "Verification/ontology-first-release"
PROJECT = HERE / "fixtures/edition-depot/Projects/Prior-Edition"
sys.path.insert(0, str(PROJECT / ".agents/skills/ontology/scripts"))
sys.path.insert(0, str(PROJECT / ".agents/skills/memory/scripts"))

from ontology_core import OntologyError, canonical_bytes, sha256
from ontology_publication import preview, publish
from ontology_memory import link_memory, read_links
from ontology_knowledge import knowledge
from memory_core import load_config, load_record, render_record, json_bytes
from memory_publish import transaction_payload, publish as publish_memory


def snapshot(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def save(name, value):
    target = PROJECT / "Verification/memory-ontology" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(canonical_bytes(value))
    return target.relative_to(PROJECT).as_posix()


def main(roster_file):
    roster = json.loads(Path(roster_file).read_text())
    now = datetime.now(timezone.utc)
    before_memory = snapshot(PROJECT / "MEMORY")
    before_memory_config = sha256(PROJECT / "memory.yaml")
    config_path = PROJECT / "ontology.yaml"
    config = json.loads(config_path.read_text())
    source = "docs/frozen-input-design.md"
    if source not in config["source_allowlist"]:
        config["source_allowlist"].append(source)
        config_path.write_bytes(canonical_bytes(config))
    identity = config["project"]["namespace"] + "FrozenRule"
    concept = {"@id": identity, "@type": ["urn:sys4ai:ontology:core:OntologyConcept"], "kind": "concept",
               "label": "Prior Task manager context rule", "definition": "This isolated fixture requires one immutable ontology packet for every initial solver; later live concepts cannot enter that frozen selection.",
               "lifecycle": "approved", "module": "project", "fact_kind": "asserted",
               "sources": [{"path": source, "sha256": sha256(PROJECT / source), "locator": "section:Accepted fixture design"}]}
    path = "ONTOLOGY/modules/project/project.jsonld"
    content = canonical_bytes({"@context": config["context"]["path"], "@graph": [concept]}).decode()
    payload = {"schema_version": 1, "operation_id": "ONTOP-reciprocal-acceptance-001", "operation": "publish",
               "reason": "Publish the reviewed isolated acceptance rule and observe canonical memory preservation.",
               "changes": [{"path": path, "expected_sha256": sha256(PROJECT / path), "content": content, "sha256": sha256(content.encode())}]}
    proposal_preview = preview(PROJECT, payload)
    grant = {"schema_version": 1, "grant_id": "ONTGRANT-reciprocal-acceptance-001", "project_id": "prior-edition",
             "actor_id": "/root", "actor_kind": "director", "operation": "publish", "payload_sha256": sha256(canonical_bytes(payload)),
             "preview_sha256": proposal_preview["preview_sha256"], "config_sha256": sha256(config_path), "scope": [path],
             "native_receipt": roster, "observed_at": now.isoformat(), "expires_at": (now + timedelta(minutes=5)).isoformat(),
             "task": None, "reviewed_records": [{k: payload["changes"][0][k] for k in ("path", "sha256", "expected_sha256")}]}
    invalid_grant = {**grant, "actor_kind": "worker"}
    before_ontology = snapshot(PROJECT / "ONTOLOGY")
    try:
        publish(PROJECT, payload, invalid_grant, expected_preview_sha256=proposal_preview["preview_sha256"])
        raise AssertionError("Ordinary child publication was accepted")
    except OntologyError as error:
        ordinary_rejection = error.as_dict()
        assert error.code == "publisher_forbidden", ordinary_rejection
    assert before_ontology == snapshot(PROJECT / "ONTOLOGY")
    ontology_receipt = publish(PROJECT, payload, grant, expected_preview_sha256=proposal_preview["preview_sha256"])
    assert ontology_receipt["status"] == "complete", ontology_receipt
    save("ontology-publication.json", ontology_receipt)
    assert before_memory == snapshot(PROJECT / "MEMORY") and before_memory_config == sha256(PROJECT / "memory.yaml")
    links_receipt = link_memory(PROJECT, concept_queries=["Task", identity])
    links_before = read_links(PROJECT)
    assert links_before["status"] == "current"
    assert before_memory == snapshot(PROJECT / "MEMORY")
    before_memory_publish_ontology = snapshot(PROJECT / "ONTOLOGY")
    before_memory_publish_config = sha256(config_path)

    memory_config = load_config(PROJECT)
    old_path = "MEMORY/MEM-20260909-01020304.md"
    old = load_record(PROJECT, old_path, memory_config)
    new_id = "MEM-20260909-05060708"
    operation = "MEMOP-ontology-reciprocal-supersession"
    reason = "Exercise an explicit fixture-only memory supersession while retaining historical content and canonical ontology."
    moment = datetime.now(timezone.utc).isoformat()
    successor = copy.deepcopy(old)
    successor["metadata"].update(id=new_id, title="Reviewed Task manager frozen input requirement", created=moment, modified=moment)
    successor["metadata"]["lifecycle"] = {"supersedes": [old["metadata"]["id"]], "superseded_by": None, "reason": reason}
    previous = copy.deepcopy(old)
    previous["metadata"].update(state="superseded", modified=moment)
    previous["metadata"]["lifecycle"]["superseded_by"] = new_id
    previous["metadata"]["lifecycle"]["reason"] = reason
    for record in (previous, successor):
        record["metadata"]["publication"] = {"actor_id": "/root", "actor_kind": "director", "operation_id": operation, "approved_at": moment}
    changes = []
    for path, record, expected in ((old_path, previous, old["sha256"]), ("MEMORY/" + new_id + ".md", successor, None)):
        text = render_record(record)
        changes.append({"path": path, "expected_sha256": expected, "content": text, "reviewed_record_sha256": sha256(text.encode())})
    memory_payload = transaction_payload(operation, "supersede", changes, reason)
    memory_grant = {"schema_version": 1, "grant_id": operation + "-grant", "project_id": "prior-edition", "actor_id": "/root", "actor_kind": "director",
                    "operation": "supersede", "payload_sha256": sha256(json_bytes(memory_payload)), "config_sha256": sha256(PROJECT / "memory.yaml"),
                    "scope": ["MEMORY"], "native_receipt": roster, "observed_at": now.isoformat(), "expires_at": (now + timedelta(minutes=5)).isoformat(),
                    "task": None, "reviewed_records": [{"path": c["path"], "sha256": c["reviewed_record_sha256"], "expected_sha256": c["expected_sha256"]} for c in changes], "privacy_redaction": False}
    memory_grant_file = save("memory-supersession-grant.json", memory_grant)
    save("memory-supersession-payload.json", memory_payload)
    memory_receipt = publish_memory(PROJECT, memory_payload, memory_grant_file, "/root")
    assert memory_receipt["state"] == "complete", memory_receipt
    save("memory-supersession-receipt.json", memory_receipt)
    assert before_memory_publish_ontology == snapshot(PROJECT / "ONTOLOGY") and before_memory_publish_config == sha256(config_path)
    stale = read_links(PROJECT)
    assert stale["status"] == "stale" and not stale["results"], stale
    current_memory = snapshot(PROJECT / "MEMORY")
    rebuilt = link_memory(PROJECT, concept_queries=["Task", identity])
    links_after = read_links(PROJECT)
    assert links_after["status"] == "current" and current_memory == snapshot(PROJECT / "MEMORY")
    mixed = knowledge(PROJECT, "Task manager frozen input", intent="mixed")
    assert any(r.get("source_type") == "historical_memory" and r.get("record_id") == new_id for r in mixed["results"]), mixed
    assert load_record(PROJECT, old_path, memory_config)["body"] == old["body"]
    result = {"schema_version": 1, "project_id": "prior-edition", "fixture_root": str(PROJECT),
              "ordinary_child_rejection": ordinary_rejection, "ontology_publication": ontology_receipt,
              "ontology_publish_preserved_memory": True, "link_generation_preserved_memory": True,
              "memory_publication": memory_receipt, "memory_publish_preserved_ontology": True,
              "historical_body_preserved": True, "links_before": links_before, "stale_links": stale,
              "links_after": links_after, "mixed_query": mixed, "backend_configuration_preserved": before_memory_config == sha256(PROJECT / "memory.yaml"),
              "real_root_memory_changed": False}
    (HERE / "memory-integration-observations.json").write_bytes(canonical_bytes(result))
    print(json.dumps({"ontology_publish": ontology_receipt["status"], "memory_publish": memory_receipt["state"],
                      "links": [links_before["status"], stale["status"], links_after["status"]],
                      "reciprocal_preservation": True, "ordinary_child": ordinary_rejection["code"]}, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
