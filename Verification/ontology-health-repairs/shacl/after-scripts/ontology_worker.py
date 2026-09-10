"""Supervised Darwin worker. Only bounded JSON bytes cross its trust boundary."""
from __future__ import annotations
from pathlib import Path
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import platform
import selectors
import signal
import subprocess
import sys
import threading
import time


def _rss(pid):
    lib = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
    info = ctypes.create_string_buffer(96)
    count = lib.proc_pidinfo(pid, 4, 0, info, len(info))
    if count <= 0: return None
    return int.from_bytes(info.raw[8:16], sys.byteorder)


def _sandbox(python, scripts):
    # No selected project data paths are readable: inputs arrive through a pipe.
    # Python's standard library and the explicitly provisioned package directory
    # are trusted code; system loader resources are the only other read scope.
    env = Path(python).absolute().parents[1]
    real = Path(python).resolve(strict=True)
    base = real.parent.parent
    paths = [env, base, scripts, Path('/System/Library'), Path('/usr/lib'),
             Path('/usr/share/zoneinfo'), Path('/private/var/db/timezone')]
    clauses = '\n'.join('(allow file-read* (subpath ' + json.dumps(str(p)) + '))' for p in paths)
    return '(version 1)\n(deny default)\n(allow process-exec process-fork signal sysctl-read mach-lookup)\n' + clauses + '\n(allow file-read-metadata)\n(allow file-read* (literal "/") (literal "/dev/urandom") (literal "/dev/random") (literal "/dev/null"))\n(allow file-write* (literal "/dev/null"))\n'


class _Capacity:
    """Read-only locks on explicitly provisioned slots release on host failure."""
    def __init__(self, python, count):
        self.descriptors=[]; self.acquired=False
        required=3-count
        try:
            for index in range(2):
                fd=os.open(Path(python).absolute().parents[1]/('worker-slot-'+str(index)),os.O_RDONLY|os.O_NOFOLLOW)
                try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError: os.close(fd); continue
                self.descriptors.append(fd)
                if len(self.descriptors)==required: self.acquired=True; break
        except OSError:
            self.close(); raise
        if not self.acquired: self.close()
    def close(self):
        for fd in self.descriptors: os.close(fd)
        self.descriptors=[]


def run_worker(python, operation, payload, bound, *, cancel=None):
    from ontology_core import canonical_bytes
    python = Path(python).absolute()
    failure = lambda status, message, **kw: {"status": status, "complete": False,
        "diagnostics": [{"code": status, "message": message}], **kw}
    if platform.system() != 'Darwin' or not Path('/usr/bin/sandbox-exec').is_file():
        return failure('unavailable', 'The tested Darwin OS confinement launcher is unavailable.')
    if not Path(python).is_file(): return failure('unavailable', 'Selected standards interpreter is absent.')
    try:
        if _rss(os.getpid()) is None: return failure('unavailable', 'RSS enforcement cannot observe this host.')
        capacity = _Capacity(python, bound['workers'])
    except OSError: return failure('unavailable', 'The host cannot enforce worker capacity or memory observation.')
    if not capacity.acquired:
        capacity.close(); return failure('worker_capacity', 'All selected standards workers are occupied.')
    request = canonical_bytes({"operation": operation, "payload": payload, "limits": bound})
    if len(request) > bound['input_bytes']:
        capacity.close(); return failure('resource_limit', 'Worker request exceeds input_bytes.', limit='input_bytes')
    if cancel is not None and cancel.is_set():
        capacity.close(); return failure('cancelled', 'Request was cancelled before execution.')
    scripts = Path(__file__).resolve().parent
    command = ['/usr/bin/sandbox-exec', '-p', _sandbox(python, scripts), str(python), '-I', '-S', str(scripts / 'ontology_worker.py'), '--child', str(Path(python).absolute().parents[1])]
    timeout = bound['reasoning_seconds'] if operation in {'infer', 'oracle'} else bound['query_seconds']
    started = time.monotonic(); peak = 0; out = bytearray(); err = bytearray(); stopped = None
    process = None; killed = False
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd='/', env={'PATH': '/usr/bin:/bin', 'LANG': 'en_US.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}, start_new_session=True)
        def send():
            try: process.stdin.write(request); process.stdin.close()
            except (BrokenPipeError, OSError): pass
        sender = threading.Thread(target=send, daemon=True); sender.start()
        selector = selectors.DefaultSelector()
        for stream, label in ((process.stdout, 'out'), (process.stderr, 'err')):
            os.set_blocking(stream.fileno(), False); selector.register(stream, selectors.EVENT_READ, label)
        while selector.get_map():
            rss = _rss(process.pid)
            if rss: peak = max(peak, rss)
            if cancel is not None and cancel.is_set(): stopped = ('cancelled', 'Request was cancelled.')
            elif time.monotonic() - started > timeout: stopped = ('timeout', 'Worker time budget expired.')
            elif peak > bound['rss_bytes']: stopped = ('memory_limit', 'Worker exceeded its supervised resident-memory budget.')
            if stopped is not None and process.poll() is None and not killed:
                os.killpg(process.pid, signal.SIGKILL); killed = True
            for key, _ in selector.select(0.005):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk: selector.unregister(key.fileobj); continue
                target = out if key.data == 'out' else err
                maximum = bound['output_bytes'] if key.data == 'out' else 16000
                target.extend(chunk[:max(0, maximum + 1 - len(target))])
                if len(target) > maximum: stopped = ('output_limit', 'Worker output exceeded its bounded IPC channel.')
        process.wait(timeout=1); sender.join(timeout=1)
        observation = {'platform': platform.system(), 'peak_rss_bytes': peak, 'rss_limit_bytes': bound['rss_bytes'],
            'rss_overshoot_bytes': max(0, peak-bound['rss_bytes']), 'elapsed_seconds': round(time.monotonic()-started, 4),
            'exit_code': process.returncode, 'network_allowed': False, 'project_files_readable': False, 'trace':err.decode(errors='replace')}
        if stopped: return failure(*stopped, worker=observation)
        if process.returncode: return failure('worker_failure', 'Restricted worker failed; no result is trusted.', worker=observation, stderr=err.decode(errors='replace')[:1000])
        try: result = json.loads(out)
        except (ValueError, UnicodeError): return failure('malformed_ipc', 'Worker returned invalid JSON.', worker=observation)
        if not isinstance(result, dict) or not isinstance(result.get('status'), str) or type(result.get('complete')) is not bool:
            return failure('malformed_ipc', 'Worker result did not match its envelope.', worker=observation)
        result['worker'] = observation
        return result
    except (OSError, subprocess.SubprocessError) as exc:
        return failure('worker_failure', str(exc)[:500])
    finally:
        if process is not None and process.poll() is None:
            if not killed: os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        if process is not None:
            for stream in (process.stdin,process.stdout,process.stderr):
                if stream is not None: stream.close()
        if 'selector' in locals(): selector.close()
        capacity.close()


def _child():
    # -I -S prevents caller path injection, site initialization and .pth execution.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    # Selected optional packages cannot shadow the trusted adapter or stdlib.
    sys.path.append(str(Path(sys.argv[2]) / 'lib/python3.12/site-packages'))
    from ontology_core import OntologyError, canonical_bytes, decode_json
    try:
        request = decode_json(sys.stdin.buffer.read(32 * 1024 * 1024 + 1))
        from ontology_backend import dispatch
        result = dispatch(request['operation'], request['payload'], request['limits'])
        result.setdefault('diagnostics', [])
    except MemoryError:
        result = {'status': 'memory_limit', 'complete': False, 'diagnostics': [{'code': 'memory_limit', 'message': 'Worker allocation failed.'}]}
    except OntologyError as exc:
        result = {'status': exc.code, 'complete': False, 'diagnostics': [exc.as_dict()]}
    except Exception as exc:
        result = {'status': 'processing_failure', 'complete': False, 'diagnostics': [{'code': type(exc).__name__, 'message': str(exc)[:1000]}]}
    sys.stdout.buffer.write(canonical_bytes(result))


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--child': _child()
    else: raise SystemExit('Use the supervised standards interface.')
