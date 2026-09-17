"""Selected local Git observations with bounded output and no configured helpers."""
import base64
import hashlib
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import time

from curator_events import git_oid
from curator_policy import PolicyError, digest, require, sha


def _path(raw):
    require(raw and not raw.startswith(b'/') and b'..' not in raw.split(b'/') and b'\0' not in raw,
            'git_path', 'Invalid Git path.')
    return {'path_b64': base64.b64encode(raw).decode('ascii')}


class LocalGit:
    def __init__(self, root, executable, executable_sha256, *, max_bytes=1000000, max_seconds=10):
        self.root, self.executable = Path(root), Path(executable)
        require(self.root.is_absolute() and str(self.root.resolve()) == str(self.root) and self.root.is_dir(),
                'repository_unavailable', 'Exact selected repository root is unavailable.')
        require(self.executable.is_absolute() and self.executable.is_file(), 'git_executable', 'Select a local Git executable.')
        sha(executable_sha256)
        require(hashlib.sha256(self.executable.read_bytes()).hexdigest() == executable_sha256, 'git_executable', 'Selected Git executable changed.')
        self.executable_sha256 = executable_sha256
        require(type(max_bytes) is int and 1024 <= max_bytes <= 8000000 and type(max_seconds) is int and 1 <= max_seconds <= 60,
                'git_bounds', 'Select finite Git byte and time bounds.')
        self.max_bytes, self.max_seconds = max_bytes, max_seconds
        self._root_identity = self.root.stat().st_dev, self.root.stat().st_ino
        top = self._run('rev-parse', '--show-toplevel').removesuffix(b'\n')
        require(os.fsdecode(top) == str(self.root), 'repository_root', 'Select the repository top-level root.')
        common = self._run('rev-parse', '--path-format=absolute', '--git-common-dir').removesuffix(b'\n')
        common_path = Path(os.fsdecode(common)).resolve()
        require(common_path.is_dir(), 'repository_unavailable', 'Repository metadata is unavailable.')
        self._common = common_path
        self._common_identity = common_path.stat().st_dev, common_path.stat().st_ino
        git_dir = self._run('rev-parse', '--absolute-git-dir').removesuffix(b'\n')
        self._git_dir = Path(os.fsdecode(git_dir)).resolve()
        info = self._git_dir.stat(); self._git_dir_identity = (info.st_dev, info.st_ino)
        self.repository_id = 'git-' + digest([str(self.root), self._root_identity, str(common_path), self._common_identity])

    def _run(self, *arguments, allowed=(0,)):
        require(self.root.is_dir() and (self.root.stat().st_dev, self.root.stat().st_ino) == self._root_identity,
                'repository_unavailable', 'Selected root was replaced or detached.')
        require(hashlib.sha256(self.executable.read_bytes()).hexdigest() == self.executable_sha256,
                'git_executable', 'Selected executable changed.')
        if hasattr(self, '_common'):
            require(self._common.is_dir() and (self._common.stat().st_dev, self._common.stat().st_ino) == self._common_identity,
                    'repository_unavailable', 'Repository metadata was replaced or detached.')
        # No inherited GIT_* values, credentials, global includes, pager, optional
        # index writes, lazy fetching, external diff, textconv or fsmonitor hooks.
        env = {'LC_ALL': 'C', 'LANG': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
               'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_SYSTEM': os.devnull,
               'GIT_OPTIONAL_LOCKS': '0', 'GIT_TERMINAL_PROMPT': '0',
               'GIT_NO_REPLACE_OBJECTS': '1', 'GIT_NO_LAZY_FETCH': '1',
               'GIT_ATTR_NOSYSTEM': '1'}
        cmd = [str(self.executable), '--no-pager', '-c', 'core.fsmonitor=false',
               '-c', 'core.untrackedCache=false', '-c', 'core.hooksPath=' + os.devnull,
               '-c', 'diff.external=', '-c', 'submodule.recurse=false',
               '-c', 'protocol.allow=never', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0',
               '-C', str(self.root), *arguments]
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        selector = selectors.DefaultSelector(); result = [bytearray(), bytearray()]
        deadline = time.monotonic() + self.max_seconds
        try:
            for index, stream in enumerate((proc.stdout, proc.stderr)):
                os.set_blocking(stream.fileno(), False); selector.register(stream, selectors.EVENT_READ, index)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                require(remaining > 0, 'git_timeout', 'Git observation exceeded its time bound.')
                for key, _ in selector.select(min(remaining, 0.1)):
                    data = os.read(key.fileobj.fileno(), 8192)
                    if not data: selector.unregister(key.fileobj); continue
                    result[key.data].extend(data)
                    require(sum(map(len, result)) <= self.max_bytes, 'git_output_limit', 'Git output exceeded its byte bound.')
            return_code = proc.wait(timeout=max(0.001, deadline - time.monotonic()))
            require(return_code in allowed, 'git_unavailable', 'Local Git observation failed; no missing source is treated as deletion.')
            return bytes(result[0]) if allowed == (0,) else (return_code, bytes(result[0]))
        except subprocess.TimeoutExpired as exc:
            raise PolicyError('git_timeout', 'Git observation exceeded its time bound.') from exc
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL); proc.wait()
            selector.close(); proc.stdout.close(); proc.stderr.close()

    def head(self):
        code, branch = self._run('symbolic-ref', '--quiet', 'HEAD', allowed=(0, 1))
        require(code == 0, 'branch_unselected', 'Detached HEAD needs an explicit selected branch workflow.')
        commit = self._run('rev-parse', '--verify', 'HEAD^{commit}').strip().decode('ascii'); git_oid(commit)
        tree = self._run('rev-parse', '--verify', 'HEAD^{tree}').strip().decode('ascii'); git_oid(tree)
        return {'branch': branch.removesuffix(b'\n').decode('utf-8'), 'commit': commit, 'tree': tree}

    def changed_metadata(self, *, offset=0, limit=50):
        """Stream current metadata while retaining one bounded changed-path page.

        Each pass hashes discarded rows as well as selected rows. The second
        pass verifies the whole observed listing and file metadata. Retained
        buffers/page bytes and the shared observation deadline stay bounded;
        this method never loads the complete status listing into memory.
        """
        require(type(offset) is int and offset >= 0 and type(limit) is int and 1 <= limit <= 50,
                'git_page', 'Select a nonnegative offset and at most 50 metadata rows.')
        before = self.head(); deadline = time.monotonic() + self.max_seconds
        args = ('status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignore-submodules=none',
                '--', '.', ':(exclude)control_records/curator', ':(exclude).sys4ai/curator')
        environment = {'LC_ALL': 'C', 'LANG': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
                       'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_SYSTEM': os.devnull,
                       'GIT_OPTIONAL_LOCKS': '0', 'GIT_TERMINAL_PROMPT': '0',
                       'GIT_NO_REPLACE_OBJECTS': '1', 'GIT_NO_LAZY_FETCH': '1', 'GIT_ATTR_NOSYSTEM': '1'}
        command = [str(self.executable), '--no-pager', '-c', 'core.fsmonitor=false',
                   '-c', 'core.untrackedCache=false', '-c', 'core.hooksPath=' + os.devnull,
                   '-c', 'diff.external=', '-c', 'submodule.recurse=false',
                   '-c', 'protocol.allow=never', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0',
                   '-C', str(self.root), *args]

        def stream(retain):
            process = subprocess.Popen(command, env=environment, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, start_new_session=True)
            selector = selectors.DefaultSelector(); pending = bytearray(); errors = 0
            listing = hashlib.sha256(); metadata = hashlib.sha256(); rows = []
            row = None; count = 0; scanned_bytes = 0; page_bytes = 0

            def accept(value):
                nonlocal count, page_bytes
                for item in value['paths']:
                    selected = self.root / os.fsdecode(base64.b64decode(item['path_b64']))
                    try:
                        info = selected.lstat()
                        observation = [item, info.st_dev, info.st_ino, info.st_mode, info.st_size,
                                       info.st_mtime_ns, info.st_ctime_ns]
                    except FileNotFoundError: observation = [item, None]
                    metadata.update(digest(observation).encode('ascii'))
                if retain and offset <= count < offset + limit:
                    page_bytes += len(repr(value).encode('utf-8'))
                    require(page_bytes <= self.max_bytes, 'git_page_limit', 'Selected metadata page exceeds its byte bound.')
                    rows.append(value)
                count += 1

            try:
                for channel, pipe in enumerate((process.stdout, process.stderr)):
                    os.set_blocking(pipe.fileno(), False); selector.register(pipe, selectors.EVENT_READ, channel)
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    require(remaining > 0, 'git_timeout', 'Metadata observation exceeded its shared time bound.')
                    for key, _ in selector.select(min(remaining, 0.1)):
                        capacity = self.max_bytes if key.data else self.max_bytes - len(pending)
                        require(capacity > 0, 'git_record_limit', 'A status record exceeds its retained byte bound.')
                        chunk = os.read(key.fileobj.fileno(), min(65536, capacity))
                        if not chunk: selector.unregister(key.fileobj); continue
                        if key.data:
                            errors += len(chunk)
                            require(errors <= self.max_bytes, 'git_output_limit', 'Git diagnostics exceeded their bound.')
                            continue
                        listing.update(chunk); scanned_bytes += len(chunk); pending.extend(chunk)
                        while b'\0' in pending:
                            end = pending.index(0); field = bytes(pending[:end]); del pending[:end+1]
                            if row is not None:
                                row['paths'].append(_path(field)); accept(row); row = None
                            else:
                                require(len(field) > 3 and field[2:3] == b' ', 'git_output', 'Malformed status metadata.')
                                code = field[:2].decode('ascii'); value = {'status': code, 'paths': [_path(field[3:])]}
                                if any(letter in code for letter in 'RC'): row = value
                                else: accept(value)
                            require(time.monotonic() < deadline, 'git_timeout', 'Metadata observation exceeded its shared time bound.')
                        require(len(pending) <= self.max_bytes, 'git_record_limit', 'A status record exceeds its retained byte bound.')
                require(not pending and row is None, 'git_output', 'Status metadata ended inside a record.')
                require(process.wait(timeout=max(0.001, deadline-time.monotonic())) == 0,
                        'git_unavailable', 'Current Git metadata is unavailable.')
                return {'status_sha256': listing.hexdigest(), 'metadata_sha256': metadata.hexdigest(),
                        'change_count': count, 'scanned_bytes': scanned_bytes, 'changes': rows}
            except subprocess.TimeoutExpired as error:
                raise PolicyError('git_timeout', 'Metadata observation exceeded its shared time bound.') from error
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL); process.wait()
                selector.close(); process.stdout.close(); process.stderr.close()

        first = stream(True); second = stream(False)
        require({key: value for key,value in first.items() if key != 'changes'} == {key: value for key,value in second.items() if key != 'changes'},
                'git_changed', 'Current status or file metadata changed during observation.')
        require(before == self.head(), 'git_changed', 'Repository head changed during observation.')
        require(offset <= first['change_count'], 'git_page', 'Selected metadata page is past the current inventory.')
        identity = {'repository_id': self.repository_id, **before, 'dirty': bool(first['change_count']),
                    'scope': 'changed-path-metadata', 'metadata_sha256': first['metadata_sha256'],
                    'status_sha256': first['status_sha256'], 'change_count': first['change_count']}
        result = {**identity, 'source_sha256': digest(identity)}
        result['snapshot'] = digest(result)
        next_offset = offset + len(first['changes'])
        return {**result, 'changes': first['changes'], 'offset': offset,
                'next_offset': next_offset if next_offset < first['change_count'] else None,
                'remaining_changes': first['change_count'] - next_offset,
                'scanned_bytes': first['scanned_bytes'], 'retained_byte_limit': self.max_bytes}

    def is_ancestor(self, previous, current):
        git_oid(previous); git_oid(current)
        code, _ = self._run('merge-base', '--is-ancestor', previous, current, allowed=(0, 1))
        return code == 0

    def changes(self, previous, current):
        git_oid(current)
        if previous is not None: git_oid(previous)
        args = ['diff-tree', '--no-ext-diff', '--no-textconv', '--no-commit-id', '--name-status', '-z', '-r', '-M', '--ignore-submodules=none']
        args += [previous, current] if previous is not None else ['--root', current]
        fields = self._run(*args, '--').split(b'\0')
        require(fields[-1] == b'', 'git_output', 'Expected NUL-delimited diff output.')
        fields.pop(); changes = []; index = 0
        while index < len(fields):
            code = fields[index].decode('ascii'); index += 1
            require(code and code[0] in 'ACDMRTUXB', 'git_output', 'Unknown change code.')
            count = 2 if code[0] in 'RC' else 1
            require(index + count <= len(fields), 'git_output', 'Incomplete NUL-delimited change.')
            paths = [_path(v) for v in fields[index:index + count]]; index += count
            changes.append({'status': code, 'paths': paths})
            require(len(changes) <= 5000, 'git_output_limit', 'Too many changed paths.')
        return changes

    def _inventory(self, commit):
        # These commands read index/tree metadata and pathname listings only.
        # They never compare worktree contents and cannot run conversion filters.
        tree_raw = self._run('ls-tree', '-r', '-z', '--full-tree', commit, '--')
        index_raw = self._run('ls-files', '--stage', '-z')
        other_raw = self._run('ls-files', '--others', '--exclude-standard', '-z')
        committed = {}; indexed = {}
        for raw, target, is_index in ((tree_raw, committed, False), (index_raw, indexed, True)):
            require(raw.endswith(b'\0') or not raw, 'git_output', 'Expected NUL-delimited metadata.')
            for row in raw.split(b'\0'):
                if not row: continue
                require(b'\t' in row, 'git_output', 'Malformed Git metadata.')
                metadata, name = row.split(b'\t', 1); _path(name)
                parts = metadata.split(b' ')
                require(len(parts) == 3, 'git_output', 'Malformed Git metadata fields.')
                mode = parts[0].decode('ascii')
                require(mode in ('100644', '100755'), 'git_file_unsupported',
                        'Submodules, symlinks and unsupported tree modes require a separate bounded owner adapter.')
                if is_index:
                    require(parts[2] == b'0', 'index_unmerged', 'Unmerged index entries remain held.')
                    oid = parts[1].decode('ascii')
                else:
                    require(parts[1] == b'blob', 'git_output', 'Expected a file blob.')
                    oid = parts[2].decode('ascii')
                git_oid(oid); require(name not in target, 'git_output', 'Duplicate Git pathname.')
                target[name] = {'mode': mode, 'oid': oid}
        require(other_raw.endswith(b'\0') or not other_raw, 'git_output', 'Expected NUL-delimited untracked names.')
        others = [name for name in other_raw.split(b'\0') if name]
        for name in others: _path(name)
        names = sorted(set(committed) | set(indexed) | set(others))
        require(len(names) <= 500, 'git_file_limit', 'Snapshot file inventory exceeds 500 paths.')
        return committed, indexed, names, (tree_raw, index_raw, other_raw)

    def snapshot(self):
        before = self.head()
        committed, indexed, names, inventory = self._inventory(before['commit'])
        directories = {}; directory_bindings = []; files = []; opened_files = []
        index_directories = []; index_directory_bindings = []; index_fd = None
        total = 0; rows = []

        def identity(info):
            return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
                    info.st_mtime_ns, info.st_ctime_ns)

        def capacity():
            require(len(directories) + len(index_directories) + len(opened_files) < 128, 'git_descriptor_limit',
                    'Snapshot exceeds the 128 retained-descriptor bound.')

        def walk_parent(parts):
            prefix = (); parent = directories[prefix]
            require(len(parts) <= 32, 'git_path_limit', 'Snapshot path exceeds 32 components.')
            for part in parts[:-1]:
                key = (*prefix, part)
                if key not in directories:
                    capacity()
                    try: fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                    except FileNotFoundError: return None
                    info = os.fstat(fd); directories[key] = fd
                    directory_bindings.append((parent, part, fd, identity(info)))
                parent = directories[key]; prefix = key
            return parent

        def read_content(fd, size):
            os.lseek(fd, 0, os.SEEK_SET); raw = bytearray()
            while True:
                part = os.read(fd, min(8192, size + 1 - len(raw)))
                if not part: break
                raw.extend(part)
                require(len(raw) <= size, 'git_changed', 'Source grew during snapshot.')
            require(len(raw) == size, 'git_changed', 'Source shrank during snapshot.')
            return bytes(raw)

        def read_index():
            nonlocal index_fd
            expected = self._git_dir / 'index'
            location = self._run('rev-parse', '--path-format=absolute', '--git-path', 'index').removesuffix(b'\n')
            require(os.fsdecode(location) == str(expected), 'git_index_location', 'Index location differs from selected Git metadata.')
            require(not self._run('rev-parse', '--shared-index-path').strip(), 'split_index_unsupported',
                    'Split-index dependencies require a separately bounded index adapter.')
            parent = os.open(b'/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            index_directories.append(parent)
            for part in os.fsencode(str(self._git_dir)).split(b'/')[1:]:
                capacity()
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                info = os.fstat(child); index_directories.append(child)
                index_directory_bindings.append((parent, part, child, (info.st_dev, info.st_ino, info.st_mode)))
                parent = child
            info = os.fstat(parent)
            require((info.st_dev, info.st_ino) == self._git_dir_identity, 'git_index_location', 'Selected Git metadata directory was replaced.')
            capacity()
            index_fd = os.open(b'index', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            opened_files.append(index_fd); info = os.fstat(index_fd)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= self.max_bytes,
                    'git_index_limit', 'Index is unsafe or exceeds the selected byte bound.')
            raw = read_content(index_fd, info.st_size)
            require(raw.startswith(b'DIRC'), 'git_index_invalid', 'Expected a Git index file.')
            return parent, identity(info), hashlib.sha256(raw).hexdigest()

        def verify_index():
            for parent, name, fd, expected in index_directory_bindings:
                named = os.stat(name, dir_fd=parent, follow_symlinks=False); opened = os.fstat(fd)
                require((named.st_dev, named.st_ino, named.st_mode) == expected
                        and (opened.st_dev, opened.st_ino, opened.st_mode) == expected,
                        'git_changed', 'An index ancestor directory changed or was replaced.')
            named = os.stat(b'index', dir_fd=index_parent, follow_symlinks=False)
            require(identity(named) == index_identity, 'git_changed', 'Index pathname changed or was replaced.')
            if index_fd in opened_files:
                require(identity(os.fstat(index_fd)) == index_identity, 'git_changed', 'Index descriptor changed.')

        def verify_names():
            root_now = os.stat(self.root, follow_symlinks=False)
            require(identity(root_now) == identity(root_info),
                    'repository_unavailable', 'Repository root changed during observation.')
            for parent, name, fd, expected in directory_bindings:
                current = os.stat(name, dir_fd=parent, follow_symlinks=False)
                require(identity(current) == expected and identity(os.fstat(fd)) == expected,
                        'git_changed', 'A source directory changed or was replaced.')
            for parent, name, fd, expected, raw_path in files:
                if parent is None:
                    require(walk_parent(raw_path.split(b'/')) is None, 'git_changed', 'A missing source directory appeared.')
                    continue
                try: current = os.stat(name, dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError: current = None
                require((None if current is None else identity(current)) == expected,
                        'git_changed', 'A source pathname changed or was replaced.')
                if fd is not None and fd in opened_files:
                    require(identity(os.fstat(fd)) == expected, 'git_changed', 'A source descriptor changed.')
        try:
            root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            directories[()] = root_fd
            root_info = os.fstat(root_fd)
            require((root_info.st_dev, root_info.st_ino) == self._root_identity,
                    'repository_unavailable', 'Selected root was replaced.')
            index_parent, index_identity, index_sha256 = read_index()
            for raw_path in names:
                parts = raw_path.split(b'/'); parent = walk_parent(parts); fd = None; info = None
                if parent is not None:
                    capacity()
                    try: fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                    except FileNotFoundError: pass
                if fd is None:
                    files.append((parent, parts[-1], None, None, raw_path))
                    rows.append({**_path(raw_path), 'mode': None, 'sha256': None, 'oid': None}); continue
                opened_files.append(fd); info = os.fstat(fd)
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= self.max_bytes - total,
                        'git_file_limit', 'Source is unsafe or exceeds the raw snapshot byte bound.')
                total += info.st_size; raw = read_content(fd, info.st_size)
                files.append((parent, parts[-1], fd, identity(info), raw_path))
                blob = b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw
                oid = (hashlib.sha1(blob) if len(before['commit']) == 40 else hashlib.sha256(blob)).hexdigest()
                rows.append({**_path(raw_path), 'mode': '100755' if info.st_mode & 0o111 else '100644',
                             'sha256': hashlib.sha256(raw).hexdigest(), 'oid': oid})
            require(before == self.head() and inventory == self._inventory(before['commit'])[3],
                    'git_changed', 'Repository metadata changed during observation.')
            verify_names(); verify_index()
            require(hashlib.sha256(read_content(index_fd, index_identity[4])).hexdigest() == index_sha256,
                    'git_changed', 'Index bytes changed during observation.')
            require(not self._run('rev-parse', '--shared-index-path').strip(), 'split_index_unsupported',
                    'Split-index dependencies appeared during observation.')
            for row, (_, _, fd, expected, _) in zip(rows, files):
                if fd is not None:
                    require(hashlib.sha256(read_content(fd, expected[4])).hexdigest() == row['sha256'],
                            'git_changed', 'Source bytes changed during observation.')
            verify_names(); verify_index()
            # Close content descriptors only after byte/identity verification, then
            # recheck names through retained parents. This catches replacement at
            # descriptor-close boundaries without following intermediate symlinks.
            for fd in list(opened_files): os.close(fd); opened_files.remove(fd)
            verify_names(); verify_index()
            observed = {name: {'mode': row['mode'], 'oid': row['oid']}
                        for name, row in zip(names, rows) if row['mode'] is not None}
            result = {'repository_id': self.repository_id, **before, 'dirty': observed != committed or indexed != committed,
                      'worktree_sha256': digest(rows),
                      'index_sha256': index_sha256, 'index_identity_sha256': digest(index_identity)}
            result['source_sha256'] = digest([before['tree'], result['index_sha256'], result['index_identity_sha256'], result['worktree_sha256']])
            result['snapshot'] = digest(result)
            return result
        except OSError as exc:
            raise PolicyError('git_file_unavailable', 'A source or directory is unavailable or unsafe.') from exc
        finally:
            for fd in opened_files: os.close(fd)
            for fd in reversed(list(directories.values())): os.close(fd)
            for fd in reversed(index_directories): os.close(fd)
