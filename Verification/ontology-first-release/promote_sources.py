"""Promote a reviewed complete source candidate under the existing updater lock."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import stat
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Verification/ontology-first-release"
sys.path.insert(0, str(ROOT / "tools"))
import template_update as engine


def run():
    manifest = json.loads((OUT / "change-manifest.json").read_text())
    lock = engine.safe(ROOT / engine.LOCK)
    fd = os.open(lock, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        metadata = os.fstat(fd)
        assert stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
        # Wait for the current watcher/initializer to release its real lock.
        # This neither removes nor overrides the other owner's lock.
        fcntl.flock(fd, fcntl.LOCK_EX)
        for entry in manifest["source_entries"]:
            target = ROOT / entry["destination"]
            source = ROOT / entry["source"]
            actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
            assert actual == entry["before_sha256"], entry["destination"]
            assert hashlib.sha256(source.read_bytes()).hexdigest() == entry["after_sha256"], entry["source"]
        before = engine.load_state(ROOT)
        current = engine.plan(ROOT, before, engine.snapshot(ROOT)["state"])
        assert current["status"] == "current" and not current["conflicts"], current
        for entry in manifest["source_entries"]:
            engine.atomic_write(engine.safe(ROOT / entry["destination"]), engine.read_file(ROOT / entry["source"]))
        preview = engine.plan(ROOT, before, engine.snapshot(ROOT)["state"])
        (OUT / "live-template-reviewed-preview.json").write_text(json.dumps(preview, indent=2) + "\n")
        assert not preview["conflicts"] and not preview["deletions"], preview
        result = {"status": "applied", "plan_id": manifest["plan_id"],
                  "manifest_sha256": hashlib.sha256((OUT / "change-manifest.json").read_bytes()).hexdigest(),
                  "files": len(manifest["source_entries"]),
                  "template_preview": "Verification/ontology-first-release/live-template-reviewed-preview.json",
                  "publication_guard": "Existing Template updater exclusive advisory lock held across coordinated source promotion; waited for the prior holder to release it."}
        (OUT / "source-promotion-receipt.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
