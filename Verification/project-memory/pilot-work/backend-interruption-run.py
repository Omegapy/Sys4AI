"""Interrupt one real vendor process after it creates only its staged database."""
import importlib.util
import json
from pathlib import Path
import subprocess
import time

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pilot", BASE / "backend-fixture-run.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
import basic_memory_adapter as adapter
from basic_memory_projection import canonical_json
from memory_core import load_config
from memory_maintenance import reindex_payload, reindex, pending_reindexes, recover_reindex
from memory_paths import MemoryError

root = pilot.fixture("alpha")
config = load_config(root)
payload = reindex_payload(root)
grant_file, sha = pilot.grant(root, payload, "actual-interruption-" + str(time.time_ns()))
before = pilot.snapshot(root, True)
receipt = {}
original_runner = adapter.run_worker


def interrupt_actual_worker(root, config, request, *, build=False):
    assert build
    command = [adapter._runtime_python(root), "-B", str(Path(adapter.__file__).resolve()), "--build-worker"]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            cwd=root, env=adapter._worker_environment(root, config))
    proc.stdin.write(canonical_json(request))
    proc.stdin.close()
    started = time.perf_counter()
    database = root / request["database"]
    while proc.poll() is None and not database.exists() and time.perf_counter() - started < 25:
        time.sleep(0.005)
    receipt.update(pid=proc.pid, command=command, staged_database=request["database"], database_observed=database.exists(),
                   seconds_before_stop=time.perf_counter() - started)
    if proc.poll() is None:
        proc.terminate()
    receipt["returncode"] = proc.wait(timeout=10)
    receipt["stdout"] = proc.stdout.read().decode(errors="replace")[-2000:]
    receipt["stderr"] = proc.stderr.read().decode(errors="replace")[-2000:]
    raise MemoryError("pilot_worker_interrupted", "Actual vendor process deliberately terminated after staged database creation.", receipt)


try:
    adapter.run_worker = interrupt_actual_worker
    reindex(root, grant_file=grant_file, actor=pilot.ACTOR, expected_payload_sha256=sha)
except MemoryError as exc:
    result = {"schema_version": 1, "level": "actual-vendor-process-interruption", "error": exc.as_dict(), "process": receipt,
              "canonical_preserved": before == pilot.snapshot(root, True)}
finally:
    adapter.run_worker = original_runner

pending = pending_reindexes(root, config)
result["pending"] = [{"operation_id": j["operation_id"], "status": j["status"]} for j in pending]
read_before = pilot.snapshot(root)
result["health_while_pending"] = adapter.health(root)
result["pending_read_preserved"] = read_before == pilot.snapshot(root)
for journal in pending:
    grant_file, sha = pilot.grant(root, journal["payload"], "actual-recovery-" + journal["operation_id"])
    result["recovery"] = recover_reindex(root, journal["operation_id"], grant_file=grant_file, actor=pilot.ACTOR)
result["restored_health"] = adapter.health(root)
result["restored_hybrid"] = adapter.query(root, "passive satellite cooling")
result["canonical_preserved_after_recovery"] = before == pilot.snapshot(root, True)
(BASE.parent / "backend-interruption-results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k not in {"error", "restored_hybrid"}}, indent=2))
