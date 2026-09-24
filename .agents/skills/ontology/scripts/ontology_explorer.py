"""Closed loopback knowledge reader. Startup is explicit; requests are read-only."""
from __future__ import annotations
import sys
# The public CLI normally supplies the verified -c bootstrap. Direct explicit
# invocation must also remove ambient discovery before stdlib imports.
if __name__ == '__main__' and not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
    if 'posix' not in sys.builtin_module_names:
        sys.stdout.write('{"status":"unavailable","error":"resource_limit"}\n')
        raise SystemExit(2)
    import posix
    posix.execve(sys.executable,[sys.executable,'-I','-S','-B',__file__,*sys.argv[1:]],
                 {'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8','PYTHONDONTWRITEBYTECODE':'1'})
import argparse
import base64
import ctypes
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import socket
import stat
import subprocess
import sys
import time
import types

IDENTITY = 'sys4ai-project-knowledge-explorer'
API = '/api/explorer/v1/'
OPERATIONS = ('context', 'search', 'entry', 'relationships', 'neighborhood', 'source')
CLOSURE = ('ontology_core', 'ontology_modules', 'ontology_validate', 'ontology_retrieval',
           'ontology_explorer_snapshot', 'ontology_explorer_source', 'ontology_explorer_read',
           'ontology_explorer_assets', 'ontology_explorer', 'ontology_explorer_worker', 'ontology_explorer_health')
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; style-src-elem 'self'; style-src-attr 'none'; img-src 'none'; font-src 'none'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; worker-src 'none'"
TOKEN = re.compile(r'[A-Za-z0-9_-]{43}\Z')
DIGEST = re.compile(r'[a-f0-9]{64}\Z')
REQUEST_ID = re.compile(r'[A-Za-z0-9-]{1,32}\Z')
_LIBPROC = None
# This fixed interpreter-only bootstrap executes exactly captured, hashed source.
# The first invocation is only a launcher; it never accepts sockets or sessions.
BOOTSTRAP = r'''import os,sys,stat,hashlib,types,json
p=sys.argv[1]; expected=sys.argv[2]
try:
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  s=os.fstat(fd)
  if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_size>2000000: raise ValueError()
  raw=os.read(fd,2000001)
  if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError()
 finally: os.close(fd)
except (OSError,ValueError):
 if sys.argv[4:]==['--worker']:
  body=b'{"kind":"failed","code":"package_changed"}'
  os.write(1,len(body).to_bytes(4,'big')+body)
 else:
  print('{"status":"unavailable","error":"package_changed"}')
 sys.exit(2)
m=types.ModuleType('_explorer_boot');m.__file__=p;sys.modules[m.__name__]=m
exec(compile(raw,p,'exec',dont_inherit=True),m.__dict__)
sys.exit(m.verified_entry(sys.argv[4:],raw,sys.argv[3]))
'''


class ServiceError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def need(value, code='invalid_request'):
    if not value: raise ServiceError(code)


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def strict(raw, *, members=256, arrays=32, max_depth=16):
    def pairs(items):
        result = {}
        for k, v in items:
            need(k not in result)
            result[k] = v
        return result
    def reject(value): raise ServiceError('invalid_request')
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=reject)
        def check(v, depth=0):
            need(depth <= max_depth)
            if isinstance(v, dict):
                need(len(v) <= members)
                for k, x in v.items(): k.encode('utf-8'); check(x, depth + 1)
            elif isinstance(v, list):
                need(len(v) <= arrays)
                for x in v: check(x, depth + 1)
            elif isinstance(v, str): v.encode('utf-8')
            elif type(v) is int: need(abs(v) <= 9007199254740991)
            elif type(v) is float: need(math.isfinite(v))
        check(value)
        return value
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise ServiceError('invalid_request') from None


def token(): return base64.urlsafe_b64encode(os.urandom(32)).decode('ascii').rstrip('=')


def is_token(value):
    if not isinstance(value, str) or not TOKEN.fullmatch(value): return False
    try: return base64.urlsafe_b64encode(base64.urlsafe_b64decode(value + '=')).decode().rstrip('=') == value
    except ValueError: return False


def directory(path):
    path = Path(path).absolute()
    need(path == path.resolve(strict=True), 'identity_mismatch')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = nxt
        return fd
    except BaseException:
        os.close(fd); raise


def read_file(path, limit=2_000_000):
    path = Path(path).absolute(); parent = directory(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            before = os.fstat(fd)
            need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit, 'package_incomplete')
            raw = bytearray()
            while len(raw) <= limit:
                part = os.read(fd, min(65536, limit + 1 - len(raw)))
                if not part: break
                raw.extend(part)
            after = os.fstat(fd); named = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            need(len(raw) <= limit and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                 (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) and
                 (after.st_dev, after.st_ino) == (named.st_dev, named.st_ino), 'package_changed')
            return bytes(raw)
        finally: os.close(fd)
    finally: os.close(parent)


def schema_location(scripts):
    # Fixed source and installed layouts only; never a browser/config path.
    scripts = Path(scripts)
    need(scripts.name == 'scripts' and scripts.parent.name == 'ontology', 'package_incomplete')
    if scripts.parent.parent.name == 'SKILLS-depo':
        return scripts.parents[2] / 'ONTOLOGY-depo/schema/explorer-v1.json'
    need(scripts.parents[1].name == 'skills' and scripts.parents[2].name == '.agents', 'package_incomplete')
    return scripts.parents[3] / 'reference-assets/ONTOLOGY-depo/schema/explorer-v1.json'


def prepare_package(scripts, *, expected_source=None, expected_snapshot=None, expected_manifest=None):
    scripts = Path(scripts).absolute()
    raw = read_file(scripts / 'ontology_explorer_snapshot.py')
    if expected_snapshot is not None:
        need(hashlib.sha256(raw).hexdigest() == expected_snapshot, 'package_changed')
    module = types.ModuleType('_explorer_snapshot_boot')
    module.__file__ = str(scripts / 'ontology_explorer_snapshot.py')
    sys.modules[module.__name__] = module
    exec(compile(raw, module.__file__, 'exec', dont_inherit=True), module.__dict__)
    explorer = scripts.parent / 'explorer'; schema = schema_location(scripts)
    manifest_raw = read_file(explorer / 'assets/manifest.json', 131072)
    manifest = strict(manifest_raw, arrays=64)
    need(isinstance(manifest, dict) and isinstance(manifest.get('assets'), list), 'package_incomplete')
    files = {'schema': schema, 'manifest': explorer / 'assets/manifest.json'}
    for name in ('package.json', 'package-lock.json', 'THIRD_PARTY_NOTICES.md', 'BUILD.md'):
        files[name] = explorer / name
    for item in manifest['assets']:
        need(isinstance(item, dict) and isinstance(item.get('path'), str), 'package_incomplete')
        path = item['path']
        need(re.fullmatch(r'[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*', path) and all(p not in ('.', '..') for p in path.split('/')), 'package_incomplete')
        files['asset:' + path] = explorer / 'assets' / path
    package = module.VerifiedPackage(scripts, files, allowed_modules=CLOSURE)
    need(package.raw['ontology_explorer_snapshot.py'] == raw, 'package_changed')
    if expected_manifest is not None:
        need(package.manifest == expected_manifest, 'package_changed')
    if expected_source is not None:
        need(package.raw['ontology_explorer.py'] == expected_source, 'package_changed')
    # No unknown ambient project modules participate. All runtime modules are
    # compiled from the same captured package in both supervisor and worker.
    for name in CLOSURE: package.load(name)
    assets = package.modules['ontology_explorer_assets']
    asset_package = assets.load_assets(explorer / 'assets',
        schema_sha256=hashlib.sha256(package.member_bytes['schema']).hexdigest(),
        lock_path=files['package-lock.json'], notices_path=files['THIRD_PARTY_NOTICES.md'])
    package.verify()
    return package, asset_package


def rss_bytes(pid):
    global _LIBPROC
    if sys.platform == 'darwin':
        if _LIBPROC is None:_LIBPROC = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
        info = ctypes.create_string_buffer(96)
        count = _LIBPROC.proc_pidinfo(pid, 4, 0, info, len(info))
        return int.from_bytes(info.raw[8:16], sys.byteorder) if count == 96 else None
    if sys.platform.startswith('linux'):
        try:
            value = Path('/proc', str(pid), 'statm').read_text().split()
            return int(value[1]) * os.sysconf('SC_PAGE_SIZE')
        except (OSError, ValueError, IndexError): return None
    return None


def sanitized_environment():
    return {'PATH': '/usr/bin:/bin', 'LANG': 'en_US.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}


class PipeWorker:
    """One process, bounded framed pipes, no shell or optional worker profile."""
    def __init__(self, package, root, instance, started, secret):
        self.package, self.root = package, str(root)
        self.instance, self.started, self.secret = instance, started, secret
        self.process = None; self.buffer = bytearray(); self.outgoing = bytearray()
        self.peak = 0; self.parent_peak = 0; self.observations = 0; self.max_observation_gap = 0.0; self.last_observed = None; self.last_start = -float('inf')
        self.ready = None; self.handshake = None

    def start(self, deadline, *, initial=False):
        need(self.process is None, 'service_busy')
        need(initial or time.monotonic() - self.last_start >= 30, 'service_busy')
        parent_rss = rss_bytes(os.getpid())
        need(parent_rss is not None and parent_rss <= 64 * 1024**2, 'resource_limit')
        self.package.verify()
        self.last_start = time.monotonic()
        self.process = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c', BOOTSTRAP,
            str(self.package.scripts / 'ontology_explorer.py'), self.package.helpers['ontology_explorer.py'], self.package.helpers['ontology_explorer_snapshot.py'], '--worker'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            cwd='/', env=sanitized_environment(), start_new_session=True, bufsize=0)
        for stream in (self.process.stdin, self.process.stdout): os.set_blocking(stream.fileno(), False)
        self.buffer.clear(); self.outgoing.clear(); self.ready = None
        self.send({'kind': 'start', 'root': self.root, 'manifest': self.package.manifest,
                   'epoch': self.package.code_epoch, 'instance': self.instance, 'started': self.started,
                   'secret': base64.b64encode(self.secret).decode(), 'deadline': deadline})

    def send(self, value):
        raw = compact(value)
        need(len(raw) <= 131072 and not self.outgoing, 'resource_limit')
        self.outgoing.extend(len(raw).to_bytes(4, 'big') + raw)

    def pump(self):
        need(self.process is not None, 'internal_error')
        while True:
            try: part = os.read(self.process.stdout.fileno(), min(65536, 131077 - len(self.buffer)))
            except BlockingIOError: break
            if not part:
                need(self.buffer, 'internal_error'); break
            self.buffer.extend(part)
            need(len(self.buffer) <= 131076, 'resource_limit')
            if len(self.buffer) >= 4:
                size = int.from_bytes(self.buffer[:4], 'big')
                need(0 < size <= 131072, 'resource_limit')
                if len(self.buffer) >= size + 4:
                    need(len(self.buffer) == size + 4, 'invalid_request')
                    raw = bytes(self.buffer[4:]); self.buffer.clear()
                    return strict(raw, arrays=100000, members=100000, max_depth=17)
        if self.outgoing:
            try:
                n = os.write(self.process.stdin.fileno(), self.outgoing)
                del self.outgoing[:n]
            except BlockingIOError: pass
            except OSError: raise ServiceError('internal_error') from None
        need(self.process.poll() is None, 'internal_error')
        return None

    def observe(self):
        now=time.monotonic()
        if self.last_observed is not None:self.max_observation_gap=max(self.max_observation_gap,now-self.last_observed)
        self.last_observed=now;self.observations+=1
        parent = rss_bytes(os.getpid())
        need(parent is not None, 'resource_limit')
        self.parent_peak = max(self.parent_peak, parent)
        need(parent <= 64 * 1024**2, 'resource_limit')
        if self.process:
            value = rss_bytes(self.process.pid)
            if value is None and self.process.poll() is not None:return
            need(value is not None, 'resource_limit')
            self.peak = max(self.peak, value)
            need(value <= 256 * 1024**2, 'resource_limit')

    def accept(self, value):
        need(isinstance(value, dict), 'internal_error')
        if value.get('kind') == 'failed': raise ServiceError(value.get('code', 'internal_error'))
        need(value.get('epoch') == self.package.code_epoch and value.get('loaded') == self.package.loaded_digests, 'package_changed')
        self.package.verify()
        self.handshake = {'epoch': value['epoch'], 'loaded': value['loaded']}
        return value

    def wait_ready(self, deadline):
        try:
            while time.monotonic() < deadline:
                value = self.pump()
                if value is not None:
                    value = self.accept(value)
                    need(value.get('kind') == 'ready', 'internal_error')
                    self.ready = value; return value
                self.observe()
                time.sleep(min(.01, max(0, deadline - time.monotonic())))
            raise ServiceError('deadline_exceeded')
        except BaseException:
            self.stop(); raise

    def stop(self):
        process, self.process = self.process, None
        if process:
            if process.poll() is None: process.kill()
            process.wait(timeout=2)
            process.stdin.close(); process.stdout.close()
        self.buffer.clear(); self.outgoing.clear()


class PrivateFiles:
    """Create only per-instance files and remove only their unchanged identities."""
    def __init__(self, root):
        self.root = Path(root); self.files = []; self.created_directories = []; self.fd = None
        fd = directory(self.root)
        try:
            current = self.root
            for part in ('.sys4ai', 'ontology', 'explorer'):
                current = current / part
                try:
                    os.mkdir(part, 0o700, dir_fd=fd)
                    self.created_directories.append(str(current.relative_to(self.root)))
                except FileExistsError: pass
                nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd); fd = nxt
            need(stat.S_IMODE(os.fstat(fd).st_mode) == 0o700 and os.fstat(fd).st_uid == os.getuid(), 'package_incomplete')
            self.fd = fd; fd = None
        finally:
            if fd is not None: os.close(fd)
        self.path = self.root / '.sys4ai/ontology/explorer'

    def create(self, name, value):
        need(re.fullmatch(r'[A-Za-z0-9_-]+\.json', name), 'invalid_request')
        raw = compact(value); need(len(raw) <= 8192)
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.fd)
        try:
            os.fchmod(fd, 0o600)
            view = memoryview(raw)
            while view: view = view[os.write(fd, view):]
            os.fsync(fd); st = os.fstat(fd)
        finally: os.close(fd)
        self.files.append((name, st.st_dev, st.st_ino, raw))
        return self.path / name

    def close(self):
        if self.fd is None: return
        for name, dev, ino, raw in self.files:
            try:
                st = os.stat(name, dir_fd=self.fd, follow_symlinks=False)
                if (st.st_dev, st.st_ino) == (dev, ino) and read_file(self.path / name, 8192) == raw:
                    os.unlink(name, dir_fd=self.fd)
            except (OSError, ServiceError): pass
        os.close(self.fd); self.fd = None


class Connection:
    def __init__(self, sock):
        self.sock = sock; self.accepted = time.monotonic()
        self.input = bytearray(); self.output = bytearray(); self.headers = None
        self.method = None; self.target = None; self.body_size = 0; self.closed = False
        self.stage = 'headers'; self.sent_at = None; self.job = None
        self.operation = None; self.request_id = None; self.authenticated = False


class Service:
    def __init__(self, package, assets, root, port=0, *, session_file=None):
        self.package, self.assets, self.root = package, assets, Path(root).absolute()
        self.module = package.modules['ontology_explorer_read']
        self.schema = strict(package.member_bytes['schema'], arrays=512, members=1024)
        self.errors = {r['properties']['code']['const']: ({k:v['const'] for k,v in r['properties'].items()}, r['x-http-status'])
                       for r in self.schema['$defs']['Error']['oneOf']}
        self.instance = os.urandom(16).hex(); self.started = time.monotonic(); self.changed = False
        self.sessions = {}; self.bootstraps = {}; self.stopping = False
        self.worker = PipeWorker(package, self.root, self.instance, self.started, os.urandom(32))
        self.connections = {}; self.active = None; self.waiting = None; self.listener = None
        self.private = None; self.bootstrap_file = None; self.identity_file = None
        self.root_fd = directory(self.root); st = os.fstat(self.root_fd); self.root_identity = (st.st_dev, st.st_ino)
        self.policy = {}; self.last_observation = 0; self.failure = None; self.parent_exhausted = False
        try:
            self.worker.start(self.started + 5, initial=True)
            ready = self.worker.wait_ready(self.started + 5)
            self.policy = ready['policy']; self.project = ready['project']; self.root_scope = ready['root_scope_id']
            self.stale = ready['stale']
            self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener.bind(('127.0.0.1', port)); self.listener.listen(8); self.listener.setblocking(False)
            self.port = self.listener.getsockname()[1]; self.origin = f'http://127.0.0.1:{self.port}'
            self.cookie = f'sys4ai_explorer_{self.port}_{self.instance}'
            self.private = PrivateFiles(self.root)
            name = f'bootstrap-{self.instance}.json'
            if session_file is not None:
                selected = Path(session_file)
                chosen = selected.absolute() if selected.is_absolute() else self.root / selected
                need(chosen.parent == self.private.path and chosen == chosen.resolve(strict=False), 'invalid_request')
                name = chosen.name
            initial = self.new_bootstrap()
            self.bootstrap_file = self.private.create(name, {'schema_version':1, 'service_instance':self.instance,
                'url':self.origin + '/' + '#bootstrap=' + initial, 'expires_in':60})
            self.identity_file = self.private.create(f'service-{self.instance}.json', {'schema_version':1,
                'service':IDENTITY, 'service_instance':self.instance, 'origin':self.origin, 'pid':os.getpid(),
                'project_id':self.project, 'root_scope_id':self.root_scope})
            self.verify()
        except BaseException:
            self.close(); raise

    def now(self): return time.monotonic()

    def verify(self):
        if self.changed: raise ServiceError('package_changed')
        try:
            self.package.verify()
            fd = directory(self.root)
            try:
                st = os.fstat(fd); need((st.st_dev, st.st_ino) == self.root_identity, 'package_changed')
            finally: os.close(fd)
        except Exception:
            self.changed = True; self.sessions.clear(); self.bootstraps.clear(); self.worker.stop()
            raise ServiceError('package_changed') from None

    def admit(self):
        value = rss_bytes(os.getpid())
        if value is None or value > 64 * 1024**2:
            self.parent_exhausted = True
            if value is not None:self.worker.parent_peak=max(self.worker.parent_peak,value)
            self.worker.stop()
            for pending in (self.active,self.waiting):
                if pending:self.fail(pending,'resource_limit')
            self.active=self.waiting=None
        need(not self.parent_exhausted, 'resource_limit')

    def new_bootstrap(self):
        self.admit(); self.verify(); self.prune()
        need(len(self.bootstraps) < 4, 'service_busy')
        value = token(); self.bootstraps[value] = self.now() + 60
        return value

    def prune(self):
        now = self.now()
        self.bootstraps = {k:v for k,v in self.bootstraps.items() if now < v}
        self.sessions = {k:v for k,v in self.sessions.items() if now < v['expires']}

    def error(self, code, connection=None):
        err, status = self.errors.get(code, self.errors['internal_error'])
        op = connection.operation if connection and connection.authenticated else None
        req = connection.request_id if connection and connection.authenticated else None
        limits = dict(items=1, bytes=1024, visited_nodes=1, seconds=1)
        if op and self.policy:
            limits = dict(items=self.policy['page_items'], bytes=self.policy['response_bytes'],
                          visited_nodes=self.policy['visited_nodes'], seconds=self.policy['request_seconds'])
        return status, compact(dict(schema_version=1, request_id=req, operation=op, code_epoch=None,
            service_instance=None, session_scope=None, project=None, snapshot=None, status='error', scope={}, data=None,
            page=dict(returned=0, next_cursor=None, has_more=None, total=None), limits=limits,
            coverage=dict(complete=False,reasons=[],filter_exclusions=None,visited_nodes=None,returned_nodes=None,returned_edges=None),
            diagnostics=[], error=err))

    def response(self, c, status, raw, mime='application/json', extra=()):
        if c.closed: return
        need(len(raw) <= 8 * 1024**2, 'resource_limit')
        headers = [('Content-Type',mime + '; charset=utf-8'), ('Content-Length',str(len(raw))),
                   ('Connection','close'),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),
                   ('Referrer-Policy','no-referrer'),('Cross-Origin-Resource-Policy','same-origin'),
                   ('Content-Security-Policy',CSP), *extra]
        # Status text contains no submitted input. No request logging is enabled.
        head = f'HTTP/1.1 {status} Response\r\n' + ''.join(k+': '+v+'\r\n' for k,v in headers) + '\r\n'
        c.output = bytearray(head.encode('ascii'))
        if c.method != 'HEAD': c.output.extend(raw)
        c.stage = 'write'; c.sent_at = self.now()

    def fail(self, c, code):
        status, raw = self.error(code, c); self.response(c, status, raw)

    def health(self):
        return dict(schema_version=1, service=IDENTITY, service_instance=self.instance,
                    build_id=self.assets.manifest['build_id'], protocol=1, status='package_changed' if self.changed else 'running')

    def parse_headers(self, c):
        end = c.input.find(b'\r\n\r\n')
        if end < 0:
            first = c.input.find(b'\r\n')
            need((first if first >= 0 else len(c.input)) <= 2048, 'request_too_large')
            need(len(c.input) <= 8192, 'request_too_large'); return False
        need(end + 4 <= 8192, 'request_too_large')
        head, body = bytes(c.input[:end]), bytes(c.input[end+4:])
        lines = head.split(b'\r\n'); need(len(lines[0]) <= 2048, 'request_too_large')
        need(len(lines)-1 <= 32, 'request_too_large')
        try:
            first = lines[0].decode('ascii').split(' ')
            need(len(first) == 3 and first[2] == 'HTTP/1.1')
            c.method, c.target = first[:2]
            need(re.fullmatch(r'[A-Z]+',c.method))
            need(c.target.startswith('/') and not c.target.startswith('//') and
                 not any(x in c.target for x in ('?', '#', '%', '\\')) and
                 all(32 < ord(ch) < 127 for ch in c.target))
            headers = {}
            for line in lines[1:]:
                need(b':' in line and not line.startswith((b' ', b'\t')))
                key, value = line.decode('ascii').split(':',1)
                need(re.fullmatch(r"[!#$&'*+.^_`|~0-9A-Za-z-]+",key))
                value = value.strip(' ')
                need(all(32 <= ord(ch) < 127 for ch in value))
                key = key.lower(); need(key not in headers)
                headers[key] = value
            c.headers = headers
        except UnicodeError: raise ServiceError('invalid_request') from None
        need(headers.get('host') == f'127.0.0.1:{self.port}', 'host_forbidden')
        need('transfer-encoding' not in headers and 'expect' not in headers)
        need('origin' not in headers or headers['origin'] == self.origin, 'origin_forbidden')
        if 'sec-fetch-site' in headers:
            site = headers['sec-fetch-site']
            document = c.method in ('GET','HEAD') and (c.target in ('/','/index.html') or c.target == '/' + self.assets.manifest['entry'])
            navigation = headers.get('sec-fetch-mode') == 'navigate' and headers.get('sec-fetch-dest') == 'document'
            need(site == 'same-origin' or (document and navigation and site in ('none','cross-site','same-site')), 'origin_forbidden')
        length = headers.get('content-length','0')
        need(re.fullmatch(r'0|[1-9][0-9]{0,8}',length))
        c.body_size = int(length)
        if c.method == 'POST':
            need(headers.get('origin') == self.origin, 'origin_forbidden')
            need(headers.get('content-type','').lower() in ('application/json','application/json; charset=utf-8'), 'content_type_invalid')
            need('content-length' in headers)
            need(headers.get('sec-fetch-mode','cors') in ('cors','same-origin') and headers.get('sec-fetch-dest','empty') == 'empty','origin_forbidden')
            maximum = 1024 if c.target.startswith(API+'session') else self.policy['request_bytes']
        else: maximum = 0
        need(c.body_size <= maximum, 'request_too_large')
        need(len(body) <= c.body_size)
        c.input = bytearray(body); c.stage = 'body'; return True

    def authenticate(self, c, *, csrf=False):
        cookie = c.headers.get('cookie',''); values = {}
        for pair in cookie.split(';'):
            pair = pair.strip()
            if not pair: continue
            need('=' in pair, 'session_invalid')
            key, value = pair.split('=',1); need(key not in values,'session_invalid'); values[key] = value
        value = values.get(self.cookie)
        need(is_token(value) and value in self.sessions,'session_invalid')
        session = self.sessions[value]
        if self.now() >= session['expires']:
            del self.sessions[value]; raise ServiceError('session_expired')
        if csrf: need(hmac.compare_digest(c.headers.get('x-explorer-csrf',''),session['csrf']),'csrf_forbidden')
        return value, session

    def session_result(self, session):
        return dict(schema_version=1,status='connected',csrf=session['csrf'],session_scope=session['scope'],
            expires_in=max(1,math.ceil(session['expires']-self.now())),service_instance=self.instance,
            code_epoch=self.package.code_epoch,build_id=self.assets.manifest['build_id'],
            schema_sha256=hashlib.sha256(self.package.member_bytes['schema']).hexdigest())

    def sessions_route(self, c, op, body):
        name = {'session':'SessionRequest','session-resume':'SessionResumeRequest','session-close':'SessionCloseRequest'}[op]
        need(self.module.validate(body,name,self.schema))
        cookie = None
        if op != 'session-close':
            need(body['client_build_id'] == self.assets.manifest['build_id'] and body['schema_sha256'] ==
                 hashlib.sha256(self.package.member_bytes['schema']).hexdigest(), 'package_changed')
        if op == 'session':
            need(is_token(body['bootstrap']),'session_invalid')
            self.prune(); need(body['bootstrap'] in self.bootstraps,'session_invalid')
            previous = None
            try: previous, _ = self.authenticate(c)
            except ServiceError: pass
            need(len(self.sessions)-(1 if previous else 0) < self.policy['sessions'], 'service_busy')
            del self.bootstraps[body['bootstrap']]
            if previous: del self.sessions[previous]
            value = token(); session = {'scope':os.urandom(16).hex(), 'csrf':token(), 'created':self.now(), 'expires':self.now()+self.policy['session_seconds']}
            self.sessions[value] = session
            cookie = self.cookie+'='+value+'; HttpOnly; SameSite=Strict; Path='+API+'; Max-Age='+str(self.policy['session_seconds'])
            result = self.session_result(session)
        elif op == 'session-resume':
            _, session = self.authenticate(c); result = self.session_result(session)
        else:
            value, _ = self.authenticate(c,csrf=True)
            need(body['code_epoch'] == self.package.code_epoch,'package_changed')
            del self.sessions[value]; result = dict(schema_version=1,status='closed')
            cookie = self.cookie+'=; HttpOnly; SameSite=Strict; Path='+API+'; Max-Age=0'
        self.verify(); raw = compact(result); need(len(raw)<=1024,'internal_error')
        self.response(c,200,raw,extra=[('Set-Cookie',cookie)] if cookie else ())

    def dispatch(self, c):
        try: self.verify()
        except ServiceError:
            if c.method == 'GET' and c.target == '/health':
                self.response(c,200,compact(self.health())); return
            raise
        if c.target == '/health':
            need(c.method == 'GET','method_forbidden')
            self.response(c,200,compact(self.health())); return
        self.admit()
        if c.target.startswith(API):
            need(c.method == 'POST','method_forbidden')
            op = c.target[len(API):]
            need(op in OPERATIONS + ('session','session-resume','session-close'), 'endpoint_unavailable')
            body = strict(bytes(c.input))
            if op.startswith('session'):
                self.sessions_route(c,op,body); return
            _, session = self.authenticate(c,csrf=True); c.authenticated = True; c.operation = op
            if isinstance(body,dict) and isinstance(body.get('request_id'),str) and REQUEST_ID.fullmatch(body['request_id']):
                c.request_id = body['request_id']
            need(self.module.validate(body,op.title()+'Request',self.schema))
            need(body['code_epoch'] == self.package.code_epoch,'package_changed')
            need(self.waiting is None,'service_busy')
            job = {'kind':'read','operation':op,'request':body,'scope':session['scope'],
                   'expires':int((session['expires']-self.started)*1000),
                   'deadline':c.accepted+self.policy['request_seconds']}
            c.job = job; c.stage = 'queued'
            if self.active is None: self.start_job(c)
            else: self.waiting = c
            return
        need(c.method in ('GET','HEAD'),'method_forbidden')
        entry = self.assets.manifest['entry']
        if '/' in entry and c.target in ('/','/index.html'):
            self.response(c,307,b'',extra=[('Location','/'+entry)]); return
        raw, mime = self.package.modules['ontology_explorer_assets'].read_asset(self.assets,c.target)
        self.verify(); self.response(c,200,raw,mime)

    def start_job(self, c):
        self.admit()
        need(self.now() < c.job['deadline'],'deadline_exceeded')
        if self.worker.process is None:
            self.worker.start(c.job['deadline'])
            self.active = c; c.stage = 'restarting'
        else:
            self.worker.send(c.job); self.active = c; c.stage = 'running'

    def finish_job(self, value):
        c = self.active; need(c is not None,'internal_error')
        value = self.worker.accept(value)
        if c.stage == 'restarting':
            need(value.get('kind')=='ready','internal_error')
            self.policy = value['policy']; self.worker.ready = value
            self.worker.send(c.job); c.stage = 'running'; return
        need(value.get('kind')=='result' and set(value)=={'kind','epoch','loaded','body','policy'},'internal_error')
        body = value['body']; need(self.module.validate(body,'ReadResponse',self.schema),'internal_error')
        if body['status'] == 'error' and body['error']['code'] == 'package_changed':
            self.changed=True;self.sessions.clear();self.bootstraps.clear();self.worker.stop()
            if not c.closed:self.fail(c,'package_changed')
            self.active=None;return
        need(self.module.validate(value['policy'],'EffectivePolicy',self.schema),'internal_error')
        self.policy = value['policy']
        for session in self.sessions.values():
            session['expires']=min(session['expires'],session['created']+self.policy['session_seconds'])
        if body['status'] != 'error':
            need(body['request_id'] == c.request_id and body['operation'] == c.operation and
                 body['session_scope'] == c.job['scope'] and body['service_instance'] == self.instance and
                 body['code_epoch'] == self.package.code_epoch and body['project']['root_scope_id'] == self.root_scope,'package_changed')
        need(self.now() < c.job['deadline'],'deadline_exceeded')
        if c.closed:
            self.active = None; return
        if not any(s['scope']==c.job['scope'] and self.now()<s['expires'] for s in self.sessions.values()):
            self.fail(c,'session_expired');self.active=None;return
        self.verify(); raw = compact(body); need(len(raw)<=body['limits']['bytes'],'resource_limit')
        if body.get('error',{}):
            code = body['error']['code']
            if code == 'package_changed': self.changed = True; self.sessions.clear(); self.bootstraps.clear(); self.worker.stop()
            status = self.errors[code][1]
        else: status=200
        self.response(c,status,raw); self.active=None

    def disconnect(self, c):
        if c.closed:return
        c.closed=True; self.connections.pop(c.sock.fileno(),None); c.sock.close(); c.input.clear(); c.output.clear()
        if self.waiting is c: self.waiting=None
        # An active canceled read drains under its existing deadline. Its result
        # is discarded; cancellation does not kill another session's worker.

    def tick(self):
        now = self.now()
        if now-self.last_observation >= .01:
            self.last_observation=now
            try: self.worker.observe()
            except ServiceError as exc:
                self.failure=exc.code
                parent_rss=rss_bytes(os.getpid())
                if parent_rss is None or parent_rss>64*1024**2:self.parent_exhausted=True
                self.worker.stop()
                for c in (self.active,self.waiting):
                    if c:self.fail(c,exc.code)
                self.active=self.waiting=None
        if self.active:
            try:
                need(now < self.active.job['deadline'],'deadline_exceeded')
                value=self.worker.pump()
                if value is not None:self.finish_job(value)
            except Exception as exc:
                code='package_changed' if self.changed else getattr(exc,'code','internal_error');self.worker.stop()
                if code=='package_changed':self.changed=True;self.sessions.clear();self.bootstraps.clear()
                self.fail(self.active,code);self.active=None
                if self.waiting:self.fail(self.waiting,code);self.waiting=None
        if self.waiting and self.active is None:
            c,self.waiting=self.waiting,None
            try:self.start_job(c)
            except Exception as exc:self.fail(c,getattr(exc,'code','internal_error'))
        for c in list(self.connections.values()):
            if c.stage in ('headers','body') and now-c.accepted>=2:self.fail(c,'deadline_exceeded')
            elif c.stage=='queued' and now>=c.job['deadline']:
                self.waiting=None;self.fail(c,'deadline_exceeded')
            elif c.stage=='write' and now-c.sent_at>=2:self.disconnect(c)
            if not c.closed and now-c.accepted>=10:self.disconnect(c)

    def serve(self):
        while not self.stopping:
            self.tick()
            read=[self.listener]+[c.sock for c in self.connections.values() if c.stage!='write']
            write=[c.sock for c in self.connections.values() if c.stage=='write']
            import select
            readable,writable,_=select.select(read,write,[],.01)
            for sock in readable:
                if sock is self.listener:
                    client,_=sock.accept();client.setblocking(False)
                    if len(self.connections)>=8:client.close()
                    else:self.connections[client.fileno()]=Connection(client)
                    continue
                c=self.connections.get(sock.fileno())
                if not c:continue
                try:
                    if c.stage in ('queued','running','restarting'):
                        data=sock.recv(1,socket.MSG_PEEK)
                        if not data:self.disconnect(c)
                        else:self.disconnect(c) # No pipelining after the single accepted request.
                        continue
                    room=8193-len(c.input) if c.stage=='headers' else c.body_size-len(c.input)+1
                    data=sock.recv(max(1,min(16384,room)))
                    if not data:self.disconnect(c);continue
                    c.input.extend(data)
                    if c.stage=='headers' and not self.parse_headers(c):continue
                    need(len(c.input)<=c.body_size)
                    if len(c.input)==c.body_size:self.dispatch(c)
                except BlockingIOError:pass
                except Exception as exc:self.fail(c,getattr(exc,'code','internal_error'))
            for sock in writable:
                c=self.connections.get(sock.fileno())
                if not c:continue
                try:
                    n=sock.send(c.output);del c.output[:n]
                    if not c.output:
                        try:self.verify()
                        except ServiceError:pass
                        self.disconnect(c)
                except BlockingIOError:pass
                except OSError:self.disconnect(c)

    def close(self):
        self.stopping=True
        for c in list(self.connections.values()):self.disconnect(c)
        self.worker.stop()
        if self.listener:self.listener.close();self.listener=None
        if self.private:self.private.close()
        if self.root_fd is not None:os.close(self.root_fd);self.root_fd=None


def verified_entry(argv, raw, expected_snapshot):
    try:
        initial = None
        if argv == ['--worker']:
            def take(size):
                data = bytearray()
                while len(data) < size:
                    part = os.read(0, size-len(data))
                    if not part: raise ServiceError('internal_error')
                    data.extend(part)
                return bytes(data)
            size = int.from_bytes(take(4), 'big'); need(0 < size <= 131072, 'resource_limit')
            initial = strict(take(size), members=1024, arrays=512)
            need(isinstance(initial, dict) and isinstance(initial.get('manifest'), dict))
        package, assets=prepare_package(Path(__file__).parent,expected_source=raw,expected_snapshot=expected_snapshot,
            expected_manifest=initial['manifest'] if initial else None)
        entry=package.modules['ontology_explorer']
        if argv==['--worker']:
            return package.modules['ontology_explorer_worker'].run(package,assets,initial)
        return entry.command(argv,package,assets)
    except KeyboardInterrupt:return 130
    except Exception as exc:
        code=getattr(exc,'code','package_incomplete')
        # No parser exception, path, URL, or secret is emitted at startup.
        if 'explorer-health' in argv:
            print(json.dumps({'operation':'explorer-health','service':IDENTITY,'installed':False,
                'configured':None,'running':None,'readable':False,'stale':None,'wrong_project':None,
                'unavailable':True,'endpoint':{'status':'not_examined'},
                'local':{'status':'unavailable','error':'package_incomplete'},'mutated':False}),flush=True)
            return 1
        if argv == ['--worker']:
            message=compact({'kind':'failed','code':code})
            os.write(1,len(message).to_bytes(4,'big')+message)
            return 2
        print(json.dumps({'status':'unavailable','error':code if code in ('package_changed','identity_mismatch','configuration_needed','presentation_invalid','canonical_invalid','resource_limit','deadline_exceeded') else 'package_incomplete',
            'maintenance':'See the installed Explorer BUILD.md for explicit package maintenance.'}),flush=True)
        return 2


def command(argv,package,assets):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',required=True)
    parser.add_argument('--format',choices=('json','text'),default='json')
    sub=parser.add_subparsers(dest='command',required=True)
    launch=sub.add_parser('explore');launch.add_argument('--port',type=int,default=0)
    launch.add_argument('--session-file');launch.add_argument('--open',action='store_true')
    health=sub.add_parser('explorer-health');health.add_argument('--url')
    args=parser.parse_args(argv)
    if args.command=='explorer-health':
        result=package.modules['ontology_explorer_health'].inspect(package,assets,Path(args.project_root),args.url)
        print(json.dumps(result,sort_keys=True,indent=2));return 0 if result['readable'] is True else 1
    need(0<=args.port<=65535)
    service=Service(package,assets,args.project_root,args.port,session_file=args.session_file)
    def stop(signum,frame):service.stopping=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:
        print(json.dumps({'service':IDENTITY,'status':'running','origin':service.origin,
            'session_file':str(service.bootstrap_file),'service_instance':service.instance}),flush=True)
        if args.open:
            import webbrowser
            # Token remains in the private file and browser launch only; never stdout.
            private=strict(read_file(service.bootstrap_file,8192))
            webbrowser.open(private['url'])
        service.serve()
    finally:service.close();package.close()
    return 0


if __name__=='__main__':
    try:
        raw=read_file(Path(__file__).absolute())
        os.execve(sys.executable,[sys.executable,'-I','-S','-B','-c',BOOTSTRAP,str(Path(__file__).absolute()),
            hashlib.sha256(raw).hexdigest(),hashlib.sha256(read_file(Path(__file__).with_name('ontology_explorer_snapshot.py'))).hexdigest(),*sys.argv[1:]],sanitized_environment())
    except (OSError,ServiceError):
        print(json.dumps({'status':'unavailable','error':'package_incomplete',
            'maintenance':'See the installed Explorer BUILD.md for explicit package maintenance.'}))
        raise SystemExit(2)
