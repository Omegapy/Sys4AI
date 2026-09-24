#!/usr/bin/env python3
"""Run and manage this checkout's macOS template update watcher."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import plistlib
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time


IGNORED = {
    '.git', '.venv', 'venv', 'env', '__pycache__', '.DS_Store', '.sys4ai',
    '.pytest_cache', '.ruff_cache', '.mypy_cache', '.cache', 'node_modules',
    'dist', 'build', 'models', 'logs', '.secrets', 'secrets', '.cognee_system',
}


def ignored(name: str) -> bool:
    return (name in IGNORED or name.startswith(('._', '.env', '.#'))
            or name.endswith(('.pyc', '.pyo', '.log', '.tmp', '.swp', '~')))


def fingerprint(root: Path) -> str:
    """Cheap recursive change detection; the engine verifies actual content."""
    if not (root / 'depot/template-update.json').is_file():
        raise FileNotFoundError('The configured depot or update manifest is unavailable')
    paths = [root / 'depot/template-update.json', root / 'tools/template_update.py']
    paths.extend(sorted(root.glob('*-depo')))
    paths.append(root / 'Projects/Sys4AI-Template-Project')
    rows = []
    pending = list(paths)
    while pending:
        item = pending.pop()
        info = item.lstat()
        rows.append((str(item.relative_to(root)), info.st_mode, info.st_size,
                     info.st_mtime_ns, info.st_ino))
        if stat.S_ISDIR(info.st_mode):
            pending.extend(p for p in sorted(item.iterdir()) if not ignored(p.name))
    return hashlib.sha256(json.dumps(sorted(rows)).encode()).hexdigest()


class QuietPeriod:
    def __init__(self, settle: float, retry: float = 30.0):
        self.settle = settle
        self.retry = retry
        self.previous: str | None = None
        self.changed_at = 0.0
        self.attempted: str | None = None
        self.attempted_at = float('-inf')

    def ready(self, value: str, now: float) -> bool:
        if value != self.previous:
            self.previous, self.changed_at = value, now
            return False
        if now - self.changed_at < self.settle:
            return False
        return value != self.attempted or now - self.attempted_at >= self.retry

    def attempted_now(self, value: str, now: float) -> None:
        self.attempted, self.attempted_at = value, now


def local_state(root: Path) -> Path:
    if not (root / 'depot/template-update.json').is_file():
        raise FileNotFoundError('The configured depot is unavailable')
    result = root / '.sys4ai/template-update'
    for item in (result, result.parent, root):
        if item.is_symlink():
            raise ValueError('Watcher state must not cross a symbolic link')
    result.mkdir(parents=True, exist_ok=True)
    return result


def write_status(root: Path, value: dict) -> None:
    folder = local_state(root)
    destination = folder / 'watcher.json'
    if destination.is_symlink():
        raise ValueError('Watcher status must not be a symbolic link')
    raw = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    with tempfile.NamedTemporaryFile(dir=folder, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def engine_apply(root: Path) -> dict:
    command = [sys.executable, str(root / 'tools/template_update.py'),
               '--project-root', str(root)]
    options = {'capture_output': True, 'text': True, 'timeout': 120,
               'env': {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}}
    checked = subprocess.run([*command, 'check'], **options)
    process = (checked if checked.returncode == 0 else
               subprocess.run([*command, 'apply'], **options))
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError:
        # Do not persist raw subprocess output, which may contain file content.
        return {'status': 'error', 'message': 'Update engine returned no JSON result',
                'exit_code': process.returncode}
    result['exit_code'] = process.returncode
    return result


def watch(root: Path, interval: float, settle: float) -> int:
    running = True

    def stop(_signum, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    quiet = QuietPeriod(settle)
    last_result: dict | None = None
    last_success: float | None = None
    while running:
        try:
            value = fingerprint(root)
            now = time.monotonic()
            if quiet.ready(value, now):
                result = engine_apply(root)
                quiet.attempted_now(value, now)
                if result.get('exit_code') == 0:
                    last_success = time.time()
                write_status(root, {'pid': os.getpid(), 'checked_at': time.time(),
                                   'last_success_at': last_success, 'result': result})
                if result != last_result:
                    print(json.dumps(result, sort_keys=True), flush=True)
                last_result = result
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            # A disconnected external volume must never look like deleted sources.
            result = {'status': 'waiting', 'message': type(error).__name__}
            try:
                write_status(root, {'pid': os.getpid(), 'checked_at': time.time(),
                                   'last_success_at': last_success, 'result': result})
            except (OSError, ValueError):
                # With the volume absent, status cannot be persisted there.
                pass
            if result != last_result:
                print(json.dumps(result), flush=True)
            last_result = result
        time.sleep(interval)
    return 0


def label_for(root: Path) -> str:
    suffix = hashlib.sha256(str(root).encode()).hexdigest()[:12]
    return f'org.sys4ai.template-update.{suffix}'


def log_directory(root: Path) -> Path:
    # launchd opens these before starting Python. Keep host diagnostics available
    # when the checkout is on a removable volume or that volume is disconnected.
    return Path.home() / 'Library/Logs/Sys4AI' / label_for(root)


def configuration(root: Path, interval: float, settle: float) -> dict:
    folder = log_directory(root)
    return {
        'Label': label_for(root),
        'ProgramArguments': [sys.executable, str(root / 'tools/template_watch.py'),
                             '--project-root', str(root), 'watch',
                             '--interval', str(interval), '--settle', str(settle)],
        'RunAtLoad': True,
        'KeepAlive': True,
        'ThrottleInterval': 10,
        'ProcessType': 'Background',
        'EnvironmentVariables': {'PYTHONDONTWRITEBYTECODE': '1'},
        'StandardOutPath': str(folder / 'watcher.log'),
        'StandardErrorPath': str(folder / 'watcher-error.log'),
    }


def launchctl(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(['/bin/launchctl', *arguments], capture_output=True,
                          text=True, timeout=20)


def stop_service(service: str) -> None:
    if launchctl('print', service).returncode != 0:
        return
    if launchctl('bootout', service).returncode:
        raise ValueError('Could not stop this checkout\'s watcher')
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if launchctl('print', service).returncode != 0:
            return
        time.sleep(0.1)
    raise ValueError('Watcher is still unloading; inspect launchctl before retrying')


def agent_path(root: Path) -> Path:
    return Path.home() / 'Library/LaunchAgents' / f'{label_for(root)}.plist'


def service_status(root: Path) -> dict:
    service = f'gui/{os.getuid()}/{label_for(root)}'
    output = launchctl('print', service)
    match = re.search(r'\bstate = ([^\n]+)', output.stdout)
    pid_match = re.search(r'\bpid = (\d+)', output.stdout)
    result = {'label': label_for(root), 'loaded': output.returncode == 0,
              'state': match.group(1) if match else None, 'plist': str(agent_path(root)),
              'logs': str(log_directory(root)), 'pid': int(pid_match.group(1)) if pid_match else None}
    exit_match = re.search(r'last exit code = ([^\n]+)', output.stdout)
    result['last_exit'] = exit_match.group(1) if exit_match else None
    receipt = root / '.sys4ai/template-update/watcher.json'
    if any(item.is_symlink() for item in (receipt, receipt.parent, receipt.parent.parent)):
        raise ValueError('Watcher status path must not cross a symbolic link')
    result['depot_available'] = (root / 'depot/template-update.json').is_file()
    if receipt.is_file():
        result['last_check'] = json.loads(receipt.read_text())
        result['check_stale'] = time.time() - result['last_check'].get('checked_at', 0) > 90
    else:
        result['check_stale'] = True
    result['ready'] = bool(result['loaded'] and result['state'] == 'running'
                           and result['depot_available'] and not result['check_stale']
                           and result['pid'] is not None
                           and result.get('last_check', {}).get('pid') == result['pid']
                           and result.get('last_check', {}).get('result', {}).get('exit_code') == 0)
    return result


def install(root: Path, interval: float, settle: float) -> dict:
    if sys.platform != 'darwin':
        raise ValueError('Automatic installation requires macOS; use watch directly elsewhere')
    fingerprint(root)
    local_state(root)
    destination = agent_path(root)
    for item in (destination, *destination.parents):
        if item.is_symlink():
            raise ValueError('Launch agent path must not cross a symbolic link')
    config = configuration(root, interval, settle)
    logs = log_directory(root)
    if any(item.is_symlink() for item in (logs, *logs.parents)):
        raise ValueError('Watcher log directory must not cross a symbolic link')
    for key in ('StandardOutPath', 'StandardErrorPath'):
        log = Path(config[key])
        if log.is_symlink() or (log.exists() and not log.is_file()):
            raise ValueError('Watcher logs must be regular files, not links or devices')
    logs.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing = plistlib.loads(destination.read_bytes())
        if existing.get('Label') != config['Label'] or existing.get('ProgramArguments', [])[:4] != config['ProgramArguments'][:4]:
            raise ValueError('Existing launch agent does not belong to this checkout')
    destination.parent.mkdir(parents=True, exist_ok=True)
    service = f'gui/{os.getuid()}/{label_for(root)}'
    stop_service(service)
    destination.write_bytes(plistlib.dumps(config, sort_keys=False))
    destination.chmod(0o600)
    started = launchctl('bootstrap', f'gui/{os.getuid()}', str(destination))
    if started.returncode:
        raise ValueError(f'launchctl bootstrap failed with exit {started.returncode}; inspect the local plist and launchctl diagnostics')
    return service_status(root)


def uninstall(root: Path) -> dict:
    destination = agent_path(root)
    if any(item.is_symlink() for item in (destination, *destination.parents)):
        raise ValueError('Launch agent path must not cross a symbolic link')
    if destination.exists():
        existing = plistlib.loads(destination.read_bytes())
        if existing.get('Label') != label_for(root) or str(root / 'tools/template_watch.py') not in existing.get('ProgramArguments', []):
            raise ValueError('Existing launch agent does not belong to this checkout')
    service = f'gui/{os.getuid()}/{label_for(root)}'
    stop_service(service)
    destination.unlink(missing_ok=True)
    return service_status(root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).absolute().parents[1])
    modes = parser.add_subparsers(dest='command', required=True)
    for command in ('watch', 'install', 'status', 'uninstall'):
        mode = modes.add_parser(command)
        if command in ('watch', 'install'):
            mode.add_argument('--interval', type=float, default=1.0)
            mode.add_argument('--settle', type=float, default=2.0)
    arguments = parser.parse_args()
    root = arguments.project_root.absolute()
    try:
        if not root.is_absolute() or '..' in root.parts or any(p.is_symlink() for p in (root, *root.parents)):
            raise ValueError('Use the real absolute depot path without symbolic links or traversal')
        if arguments.command in ('watch', 'install') and any(not math.isfinite(value) or value < 0.1 for value in (arguments.interval, arguments.settle)):
            raise ValueError('Polling and settling intervals must be at least 0.1 seconds')
        if arguments.command == 'watch':
            return watch(root, arguments.interval, arguments.settle)
        if arguments.command == 'install':
            result = install(root, arguments.interval, arguments.settle)
        elif arguments.command == 'uninstall':
            result = uninstall(root)
        else:
            result = service_status(root)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'error', 'message': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
