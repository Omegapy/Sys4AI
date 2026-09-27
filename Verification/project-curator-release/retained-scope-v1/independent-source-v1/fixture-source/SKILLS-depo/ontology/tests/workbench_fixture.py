"""Disposable service fixture; caller supplies actual native evidence for browser publication."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import signal
import threading

from support import make_project, bind_director, add_records, record, write_json, CORE, read_json
from ontology_workbench import Workbench, trusted_authority


def make_workbench_project(path, *, advanced=False, install_adapters=False):
    if advanced:
        from advanced_support import make_advanced
        root = make_advanced(path)
    else:
        root = make_project(path)
    bind_director(root)
    add_records(root, [record("SampleClass", kind="concept", type_name="OntologyConcept"),
                       record("sample-artifact", aliases=["sample"], **{"@type": ["urn:sys4ai:ontology:project:example:SampleClass"]}), record("related-artifact"),
                       record("sample-class-subtype", kind="relation", type_name="Relationship",
                              subject="urn:sys4ai:ontology:project:example:SampleClass", predicate=CORE + "subtypeOf", object=CORE + "Artifact"),
                       record("sample-relation", kind="relation", type_name="Relationship",
                              subject="urn:sys4ai:ontology:project:example:sample-artifact",
                              predicate=CORE + "broader", object="urn:sys4ai:ontology:project:example:related-artifact")])
    write_json(root / "ontology-advanced.yaml", {"schema_version": 1, "project_id": "example",
        "profiles": {"standards": {"enabled": advanced}, "inference": {"enabled": advanced},
                     "guards": {"enabled": False}, "workbench": {"enabled": True, "host": "127.0.0.1", "port": 0,
                                                                  "session_seconds": 900, "max_request_bytes": 1000000}},
        "extensions": [], "limits": {}})
    if install_adapters:
        from guard_support import install_adapters as install
        install(root)
    return root


def fixture_authority(root, receipt=None, observed_at=None):
    # The default is only for contract tests and is never counted as native generation/authority evidence.
    observation = receipt or {"tool": "collaboration.list_agents", "result": {"agents": [{"agent_name": "/root", "agent_status": "running"}]}}
    return trusted_authority(root, actor_id="/root", actor_kind="director", native_receipt=observation,
                             observed_at=observed_at or datetime.now(timezone.utc).isoformat(),
                             scope=read_json(root / "ontology.yaml")["project_files"] + read_json(root / "ontology.yaml")["binding_files"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--advanced", action="store_true", help="Copy the existing certified standards environment into this disposable fixture.")
    parser.add_argument("--install-adapters", action="store_true", help="Prepare all helpers/contracts for a separately reviewed actual guard setup.")
    parser.add_argument("--native-receipt")
    parser.add_argument("--observed-at")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.create:
        if root.exists() and any(root.iterdir()):
            parser.error("--create requires an empty disposable directory")
        root = make_workbench_project(root, advanced=args.advanced, install_adapters=args.install_adapters)
    authority = fixture_authority(root, read_json(Path(args.native_receipt)), args.observed_at) if args.native_receipt and args.observed_at else None
    service = Workbench(root, authority, port=args.port).start()
    # The one-use URL is delivered to the trusted foreground caller only; do not redirect it to an evidence log.
    print(service.bootstrap_url(), flush=True)
    stopped = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    try:
        stopped.wait()
    finally:
        service.close()


if __name__ == "__main__":
    main()
