"""Apply the reviewed learning-package manifest to this active depot only."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "active-root-manifest.json"
RECEIPT = HERE / "active-root-adoption.json"
PAIRS = {
    "LEARNING-depo": "reference-assets/LEARNING-depo",
    "SKILLS-depo/what-did-you-learn": ".agents/skills/what-did-you-learn",
    "SKILLS-depo/memory": ".agents/skills/memory",
    "SKILLS-depo/init-new-project": ".agents/skills/init-new-project",
}
spec = importlib.util.spec_from_file_location("learning_root_adoption_helper", ROOT / "SKILLS-depo/init-new-project/scripts/init_new_project.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def preview():
    if MANIFEST.exists():
        raise SystemExit("A reviewed manifest already exists; inspect it and use --apply to resume.")
    baseline = json.loads((HERE / "baseline.json").read_text())
    entries = []
    for source_root, destination_root in PAIRS.items():
        old = baseline["packages"].get(destination_root, {}).get("files", {})
        for relative, raw in helper.tree_files(ROOT / source_root).items():
            source = source_root + "/" + relative
            destination = destination_root + "/" + relative
            target = helper.destination_file(ROOT, destination)
            before = helper.file_bytes(target) if target.exists() else None
            expected_before = old.get(relative, {}).get("sha256")
            if before is not None and digest(before) != expected_before:
                if source_root in {"LEARNING-depo", "SKILLS-depo/what-did-you-learn"} and before == raw:
                    continue
                raise SystemExit("Current destination differs from the protected baseline: " + destination)
            if before != raw:
                entries.append({"source": source, "destination": destination,
                                "before_sha256": digest(before) if before is not None else None,
                                "after_sha256": digest(raw), "mode": stat.S_IMODE((ROOT / source).stat().st_mode)})
    data = {"plan_id": "PLAN-20260909-2AB7D4CC", "scope": PAIRS,
            "authority": "Current explicit implementation of the exact approved plan and its scoped active-root adoption.",
            "entries": entries}
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))


def apply():
    manifest = json.loads(MANIFEST.read_text())
    if manifest["scope"] != PAIRS or manifest["plan_id"] != "PLAN-20260909-2AB7D4CC":
        raise SystemExit("Unexpected adoption scope.")
    pending = []
    for entry in manifest["entries"]:
        if not any(entry["source"].startswith(source + "/")
                   and entry["destination"] == target + entry["source"][len(source):]
                   for source, target in PAIRS.items()):
            raise SystemExit("Manifest contains an unapproved source/destination mapping.")
        raw = helper.file_bytes(helper.destination_file(ROOT, entry["source"]))
        target = helper.destination_file(ROOT, entry["destination"])
        before = helper.file_bytes(target) if target.exists() else None
        if digest(raw) != entry["after_sha256"]:
            raise SystemExit("Reviewed source changed: " + entry["source"])
        current = digest(before) if before is not None else None
        if current not in {entry["before_sha256"], entry["after_sha256"]}:
            raise SystemExit("Destination changed after review: " + entry["destination"])
        pending.append((entry, raw, target, before))
    for entry, raw, target, before in pending:
        if before != raw:
            helper.atomic_write(target, raw, before, mode=entry["mode"])
    for entry, raw, target, _ in pending:
        if helper.file_bytes(target) != raw:
            raise SystemExit("Adoption readback differs: " + entry["destination"])
    RECEIPT.write_text(json.dumps({**manifest, "status": "applied",
                                  "manifest_sha256": digest(MANIFEST.read_bytes()),
                                  "verified_files": len(pending)}, indent=2) + "\n")
    print(json.dumps({"status": "applied", "verified_files": len(pending), "receipt": str(RECEIPT)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    apply() if args.apply else preview()
