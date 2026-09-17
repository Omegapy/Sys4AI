"""Conservative source/section ownership; declarations cannot lower governance."""
from fnmatch import fnmatchcase
from hashlib import sha256
from pathlib import PurePosixPath
import unicodedata

from curator_policy import PolicyError, bounded, exact, require, sha, text, texts

CLASSES = {'documentation', 'data', 'technical', 'governance', 'generated', 'historical'}
OWNERS = {'project', 'task', 'memory', 'ontology', 'setup', 'curate'}
FLOOR = ('AGENTS.md', 'SOUL.md', 'ROLE.md', 'SPECS.md', 'SKILL.md', 'CURATOR.md', 'curator.yaml',
         'document-ownership.json', 'memory.yaml', 'ontology.yaml', 'ontology-advanced.yaml',
         'CLAUDE.md', 'GEMINI.md', '.mcp.json', '.github/copilot-instructions.md', '.cursor/*',
         '.agents/*', '.codex/*', 'Roles/*', 'control_records/*',
         '*policy*', '*validator*', '*broker*', '*grant*', '*confinement*')


def relative(path):
    text(path)
    require(not path.startswith('/') and '\\' not in path and '..' not in PurePosixPath(path).parts
            and str(PurePosixPath(path)) == path and path != '.', 'path', 'Expected a normalized relative path.')
    return unicodedata.normalize('NFC', path).casefold()


def validate_map(document):
    bounded(document); exact(document, ('schema_version', 'entries'))
    require(type(document['schema_version']) is int and document['schema_version'] == 1, 'map_version', 'Unsupported ownership map.')
    require(type(document['entries']) is list, 'map_entries', 'Expected ownership entries.')
    seen = set(); paths = set()
    for entry in document['entries']:
        exact(entry, ('id', 'path', 'pattern', 'sha256', 'class', 'owner', 'generator', 'sources', 'sections', 'interfaces'))
        text(entry['id']); require(entry['id'] not in seen, 'duplicate_identity', 'Duplicate stable identity.'); seen.add(entry['id'])
        key = relative(entry['path']); require(key not in paths, 'alias', 'Case/Unicode ownership collision.'); paths.add(key)
        require(type(entry['pattern']) is bool, 'pattern', 'Pattern selection must be explicit.')
        if entry['sha256'] is not None: sha(entry['sha256'])
        require(type(entry['class']) is str and entry['class'] in CLASSES and type(entry['owner']) is str and entry['owner'] in OWNERS, 'owner', 'Unknown class or owner.')
        text(entry['generator'], True); texts(entry['sources']); texts(entry['interfaces'])
        for source in entry['sources']: relative(source)
        require((entry['class'] == 'generated') == bool(entry['generator']), 'generator', 'Generated ownership requires one generator.')
        require(entry['class'] != 'generated' or bool(entry['sources']), 'generator', 'Generated output requires canonical sources.')
        require(type(entry['sections']) is list, 'sections', 'Expected sections.')
        ids = set()
        for section in entry['sections']:
            exact(section, ('id', 'start', 'end', 'sha256', 'class', 'owner', 'protected'))
            text(section['id']); text(section['start']); text(section['end']); sha(section['sha256'])
            require(section['id'] not in ids, 'section_duplicate', 'Duplicate section identity.'); ids.add(section['id'])
            require(type(section['class']) is str and section['class'] in CLASSES and type(section['owner']) is str and section['owner'] in OWNERS and type(section['protected']) is bool, 'section', 'Invalid section ownership.')
    return document


def classify_target(trusted_map, target_identity, proposed_ranges, snapshot):
    """Snapshot is a trusted path->bytes mapping; ranges are half-open byte offsets."""
    try:
        validate_map(trusted_map)
        exact(target_identity, ('id', 'path', 'sha256')); text(target_identity['id']); sha(target_identity['sha256'])
        path = target_identity['path']; key = relative(path)
        entries = [e for e in trusted_map['entries'] if e['id'] == target_identity['id']]
        require(len(entries) == 1, 'identity_unknown', 'Stable source identity is not bound.')
        entry = entries[0]
        require(fnmatchcase(path, entry['path']) if entry['pattern'] else path == entry['path'], 'rename_unbound', 'Rename needs a trusted identity rebind.')
        require(len([p for p in snapshot if relative(p) == key]) == 1 and path in snapshot, 'alias', 'Snapshot contains an ambiguous path.')
        raw = snapshot[path]; require(type(raw) is bytes, 'snapshot', 'Snapshot must contain exact source bytes.')
        actual = sha256(raw).hexdigest()
        require(actual == target_identity['sha256'] and entry['sha256'] == actual, 'source_changed', 'Ownership source must be exactly bound before editing.')
        require(type(proposed_ranges) is list and bool(proposed_ranges), 'ranges', 'Complete edit ranges are required.')
        ranges = []
        for pair in proposed_ranges:
            require(type(pair) is list and len(pair) == 2 and all(type(n) is int for n in pair)
                    and 0 <= pair[0] <= pair[1] <= len(raw), 'ranges', 'Invalid source byte range.')
            ranges.append(tuple(pair))
        sections = []
        for section in entry['sections']:
            start, end = section['start'].encode(), section['end'].encode()
            require(raw.count(start) == 1 and raw.count(end) == 1, 'anchor_ambiguous', 'Section anchors must be unique.')
            low = raw.index(start); high = raw.index(end) + len(end)
            require(low < high and sha256(raw[low:high]).hexdigest() == section['sha256'], 'section_changed', 'Section bytes differ.')
            require(not any(low < h and l < high for l, h, _ in sections), 'section_overlap', 'Section ownership overlaps.')
            sections.append((low, high, section))
        floor = any(fnmatchcase('/'.join(key.split('/')[i:]), p.casefold())
                    for i in range(len(key.split('/'))) for p in FLOOR)
        resolved = set()
        for low, high in ranges:
            hits = [s for l, h, s in sections if l <= low and high <= h]
            crossing = any(low < h and l < high for l, h, _ in sections) and not hits
            require(not crossing, 'mixed_patch', 'Patch crosses section ownership boundaries.')
            selected = hits[0] if hits else entry
            kind = 'governance' if floor or selected.get('protected') else selected['class']
            resolved.add((kind, selected['owner']))
        require(len(resolved) == 1, 'mixed_patch', 'Mixed ownership requires separately reviewed operations.')
        kind, owner = resolved.pop()
        if kind == 'generated':
            require(owner == 'ontology' and entry['generator'] == 'ontology.wiki', 'generator_unknown', 'Unsupported generator route.')
        if kind == 'historical': require(owner == 'task', 'history_owner', 'Historical response corrections belong to Task.')
        route = 'ontology.wiki' if kind == 'generated' else 'task.response-correction' if kind == 'historical' else owner + '.' + kind
        return {'state': 'classified', 'code': 'bound', 'class': kind, 'owner': owner,
                'route': route, 'sources': entry['sources'], 'interfaces': entry['interfaces'], 'source_sha256': actual}
    except (PolicyError, KeyError) as exc:
        return {'state': 'held', 'code': getattr(exc, 'code', 'snapshot_missing')}
