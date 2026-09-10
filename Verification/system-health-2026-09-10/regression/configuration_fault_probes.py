"""Repeat configuration controls using explicit resolved temporary roots."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
rows = []


def run(name, root, kind):
    def snapshot():
        return {str(p.relative_to(root)): [hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns]
                for p in root.rglob("*") if p.is_file()}
    before = snapshot()
    command = [str(ROOT / ".venv/bin/python"), str(ROOT / f".agents/skills/{kind}/scripts/{kind}.py"), "--project-root", str(root), "health"]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    tick = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True)
    (OUT / f"probe-{name}.stdout.log").write_bytes(result.stdout)
    (OUT / f"probe-{name}.stderr.log").write_bytes(result.stderr)
    receipt = {"name": name, "command": command, "cwd": str(ROOT), "started_at": started,
               "duration_seconds": round(time.monotonic() - tick, 6), "exit_code": result.returncode,
               "fixture_bytes_and_mtimes_unchanged": before == snapshot(),
               "stdout": f"probe-{name}.stdout.log", "stderr": f"probe-{name}.stderr.log"}
    (OUT / f"probe-{name}.receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    rows.append({**receipt, "result": json.loads(result.stdout)})


with tempfile.TemporaryDirectory(prefix="sys4ai-config-health-") as directory:
    root = Path(directory).resolve()
    run("ontology-config-absent-resolved", root, "ontology")
    (root / "ontology.yaml").write_text("{invalid json\n")
    run("ontology-config-invalid-resolved", root, "ontology")
    run("memory-config-absent-resolved", root, "memory")
(OUT / "configuration-fault-probes.json").write_text(json.dumps({"controls": rows}, indent=2) + "\n")
print(json.dumps([{ "name": r["name"], "exit_code": r["exit_code"], "result": r["result"]} for r in rows]))
