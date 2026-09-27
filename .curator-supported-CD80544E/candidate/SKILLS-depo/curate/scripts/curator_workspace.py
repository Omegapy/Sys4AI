"""One explicitly selected coordination root for a local Git family and branch.

This owner reads the existing Task helper. It never creates a second ledger or
uses timestamps to transfer an execution. Independent clones remain unsupported.
"""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat

from curator_classification import relative
from curator_confinement import file_snapshot, parent_descriptor
from curator_policy import digest, exact, require


def logical_identity(git):
    git.head()  # Recheck selected executable, checkout and metadata identities.
    common = git._common
    info = common.stat()
    return {'common_directory': str(common), 'device': info.st_dev, 'inode': info.st_ino,
            'repository_id': 'git-common-' + digest([str(common), info.st_dev, info.st_ino])}


def overlaps(left, right):
    from fnmatch import fnmatchcase
    for original_a in left:
        a = relative(original_a)
        for original_b in right:
            b = relative(original_b)
            if a == b or fnmatchcase(a, b) or fnmatchcase(b, a) or a.startswith(b.rstrip('/') + '/') or b.startswith(a.rstrip('/') + '/'):
                return True
            # Two glob patterns cannot be proved disjoint by literal comparison.
            if any(c in a for c in '*?[') and any(c in b for c in '*?['): return True
    return False


class Coordination:
    """Trusted bootstrap supplies selected LocalGit objects and the actual Task owner."""
    def __init__(self, *, checkout, coordination, selection, task_owner):
        exact(selection, ('project_id', 'branch', 'common', 'coordination_root'))
        require(type(selection['project_id']) is str and selection['project_id'], 'project_unselected', 'Select a logical project.')
        require(str(coordination.root) == selection['coordination_root'], 'coordination_root', 'Select one exact canonical root.')
        require(logical_identity(checkout) == logical_identity(coordination) == selection['common'],
                'clone_unsupported', 'Only selected linked worktrees sharing exact local common metadata are supported.')
        require(checkout.head()['branch'] == selection['branch'], 'branch_unselected', 'Checkout branch differs from selection.')
        self.checkout = checkout; self.canonical = coordination; self.selection = dict(selection); self.task = task_owner

    def check(self):
        require(logical_identity(self.checkout) == logical_identity(self.canonical) == self.selection['common'],
                'coordination_changed', 'Common Git identity changed.')
        require(self.checkout.head()['branch'] == self.selection['branch'], 'branch_changed', 'Selected branch changed.')
        return dict(self.selection)

    def owners(self, paths, *, actor=None, task_binding=None):
        """Validate canonical records directly; corruption and uncertain owners hold."""
        self.check(); root = self.canonical.root / 'Tasks'; items = []
        if not root.exists(): return {'state': 'clear', 'items': []}
        require(root.is_dir() and not root.is_symlink(), 'task_root', 'Canonical Task root is unsafe.')
        folders = list(root.iterdir()); require(len(folders) <= 1000, 'task_limit', 'Canonical Task inventory is too large.')
        for folder in sorted(folders):
            if not folder.is_dir() or folder.is_symlink():
                require(not folder.is_symlink(), 'task_path', 'Unknown linked Task entry is held.')
                continue
            if not (folder / 'task.json').exists(): continue
            state, errors, _ = self.task.validate_task_folder(folder)
            if errors:
                items.append({'task': folder.name, 'state': 'uncertain', 'reason': 'invalid_task'}); continue
            orch = state.get('orchestration')
            if not orch: continue
            known = [a for a in orch['assignments'].values()
                     if a['state'] not in ('completed', 'cancelled', 'revoked')]
            affected = [a for a in known if overlaps(paths, a.get('fit', {}).get('writes', []))]
            # A paused/uncertain canonical writer with missing scope cannot grant clearance.
            if not affected and orch.get('writer') and not known and orch.get('stage') not in ('completed', 'cancelled'):
                items.append({'task': state['task_id'], 'state': 'uncertain', 'reason': 'owner_scope_missing'}); continue
            for assignment in affected:
                own = (task_binding is not None and state['task_id'] == task_binding['task_id']
                       and state['revision'] == task_binding['revision'] and orch['execution_id'] == task_binding['execution_id']
                       and orch['generation'] == task_binding['generation'] and orch['writer'] == actor
                       and assignment['native_id'] == actor and assignment['function'] == 'manager'
                       and assignment['state'] == 'active' and orch['stage'] == 'active')
                if not own:
                    items.append({'task': state['task_id'], 'assignment': assignment['assignment_id'],
                                  'owner': assignment['native_id'], 'state': assignment['state'], 'reason': 'current_owner'})
        return {'state': 'held' if items else 'clear', 'items': items}

    @contextmanager
    def serialized(self):
        """Pre-created protected lock; no read/status path creates runtime state."""
        self.check()
        with parent_descriptor(self.canonical.root, 'control_records/curator/integration.lock') as (parent, name):
            fd = os.open(name, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            try:
                info = os.fstat(fd)
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'coordination_lock', 'Expected an owned regular lock.')
                try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    require(False, 'coordination_busy', 'Another project operation owns integration.')
                current = os.stat(name, dir_fd=parent, follow_symlinks=False)
                require((info.st_dev, info.st_ino) == (current.st_dev, current.st_ino), 'coordination_lock', 'Lock identity changed.')
                self.check(); yield
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN); os.close(fd)


def copy_candidate(source_root, destination, inputs):
    """Copy only exact selected source files into a new disposable candidate root."""
    require(type(inputs) is list and 0 < len(inputs) <= 500, 'candidate_inputs', 'Select a bounded source inventory.')
    destination = Path(destination)
    require(destination.is_absolute() and not destination.exists(), 'candidate_exists', 'Candidate destination must be new.')
    contents = {}; total = 0
    for item in inputs:
        exact(item, ('path', 'sha256')); key = relative(item['path'])
        require(not any(part in ('tasks', 'control_records', '.git', '.sys4ai') for part in key.split('/')),
                'candidate_ledger', 'Candidate sources cannot include writable ledgers, runtime or Git metadata.')
        require(key not in contents, 'candidate_alias', 'Duplicate or aliased candidate source.')
        info = file_snapshot(source_root, item['path'], 2000000)
        require(info['sha256'] == item['sha256'], 'source_changed', 'Selected source changed.')
        with parent_descriptor(source_root, item['path']) as (parent, name):
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            with os.fdopen(fd, 'rb') as stream: raw = stream.read(2000001)
        import hashlib
        require(hashlib.sha256(raw).hexdigest() == item['sha256'], 'source_changed', 'Source changed during copy.')
        total += len(raw); require(total <= 8000000, 'candidate_limit', 'Candidate exceeds its total byte bound.')
        contents[key] = (item['path'], raw)
    destination.mkdir(parents=False)
    for path, raw in contents.values():
        target = destination / path; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as out: out.write(raw)
    return {'state': 'prepared', 'root': str(destination), 'inputs': inputs, 'writable_task_ledgers': 0}
