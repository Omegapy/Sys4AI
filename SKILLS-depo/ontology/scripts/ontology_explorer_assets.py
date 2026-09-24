"""Bounded, read-only Explorer assets. No build, installation or publication path.

The manifest is package metadata, never a served asset. All opens walk directory
file descriptors without following links. Call load_assets at startup, retain its
immutable package, then read_asset for each HTTP GET/HEAD (HEAD discards bytes).
The service owns headers, authorization and sticky code-epoch invalidation.
"""
from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from types import MappingProxyType
import hashlib
import json
import os
import posixpath
import re
import stat

MAX_FILES = 64
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024
MAX_MANIFEST_BYTES = 128 * 1024
MIMES = {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
ASSET_PATH = re.compile(r"[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*\Z")
FORBIDDEN_PARTS = frozenset({".git", ".sys4ai", ".agents", ".codex", "__pycache__", "cache", "caches", "node_modules", "src", "scripts", "tests", "fixtures", "dist", "build", "tasks", "memory", "ontology", "control_records", "reference-assets", "package.json", "package-lock.json", "manifest.json", "third_party_notices.md"})
MANIFEST_KEYS = frozenset({"schema_version", "api_version", "build_id", "entry", "assets", "source_digest", "lock_sha256", "notices_sha256", "toolchain", "build_command"})
MAINTENANCE = "Run npm run build && npm run package:runtime in the selected Explorer build workspace."


class AssetError(ValueError):
    """Fixed safe errors: callers must not disclose underlying OS paths."""
    def __init__(self, reason, code="package_incomplete"):
        self.code, self.reason = code, reason
        self.maintenance = MAINTENANCE if code == "package_incomplete" else None
        super().__init__(reason)


def _need(condition, reason):
    if not condition:
        raise AssetError(reason)


def canonical_bytes(value):
    """The existing ontology_core canonical_bytes serialization, without imports."""
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _pairs(items):
    result = {}
    for key, value in items:
        _need(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def _json(data):
    _need(len(data) <= MAX_MANIFEST_BYTES, "manifest_too_large")
    # Bound nesting before invoking the recursive JSON decoder.
    depth = 0
    quoted = escaped = False
    for byte in data:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            _need(depth <= 16, "manifest_too_deep")
        elif byte in (93, 125):
            depth -= 1
    try:
        return json.loads(data.decode("utf-8", errors="strict"), object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(AssetError("invalid_json_number")))
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, AssetError):
            raise
        raise AssetError("invalid_manifest_json") from exc


def asset_path(value):
    _need(isinstance(value, str) and len(value) <= 240 and ASSET_PATH.fullmatch(value), "unsafe_asset_path")
    parts = value.split("/")
    _need(all(p not in (".", "..") and p.lower() not in FORBIDDEN_PARTS for p in parts), "forbidden_asset_path")
    _need(Path(value).suffix in MIMES, "unsupported_asset_mime")
    return value


def directory_fd(path):
    """Open every component of an absolute directory without resolving symlinks."""
    path = Path(path).absolute()
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:]:
            _need(component not in (".", ".."), "unsafe_package_directory")
            new = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        return fd
    except BaseException:
        os.close(fd)
        raise


def _read_at(root_fd, relative, limit):
    parts = relative.split("/")
    fd = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            before = os.fstat(file_fd)
            _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, "unsafe_asset_file")
            _need(0 < before.st_size <= limit, "asset_size_limit")
            chunks = []
            remaining = limit + 1
            while remaining:
                block = os.read(file_fd, min(remaining, 65536))
                if not block:
                    break
                chunks.append(block)
                remaining -= len(block)
            after = os.fstat(file_fd)
            identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_nlink)
            _need(identity(before) == identity(after), "asset_changed_during_read")
            data = b"".join(chunks)
            _need(len(data) == before.st_size and len(data) <= limit, "asset_size_limit")
            return data
        finally:
            os.close(file_fd)
    finally:
        os.close(fd)


def read_regular(path, limit):
    """Public build/test utility; no writes and no generic HTTP path exposure."""
    try:
        parent = directory_fd(Path(path).absolute().parent)
        try:
            return _read_at(parent, Path(path).name, limit)
        finally:
            os.close(parent)
    except OSError as exc:
        raise AssetError("asset_unavailable") from exc


def validate_manifest(data):
    obj = _json(data)
    _need(type(obj) is dict and set(obj) == MANIFEST_KEYS, "manifest_fields")
    _need(type(obj["schema_version"]) is int and obj["schema_version"] == 1 and type(obj["api_version"]) is int and obj["api_version"] == 1, "manifest_version")
    for key in ("build_id", "source_digest", "lock_sha256", "notices_sha256"):
        _need(isinstance(obj[key], str) and DIGEST.fullmatch(obj[key]), "manifest_digest")
    _need(type(obj["toolchain"]) is dict and set(obj["toolchain"]) == {"node", "npm"}, "toolchain_fields")
    _need(obj["toolchain"]["node"] == "25.9.0" and isinstance(obj["toolchain"]["npm"], str) and len(obj["toolchain"]["npm"]) <= 80 and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", obj["toolchain"]["npm"]), "toolchain_version")
    _need(obj["build_command"] == "npm run build && npm run package:runtime", "build_command")
    _need(type(obj["assets"]) is list and 1 <= len(obj["assets"]) <= MAX_FILES, "asset_count_limit")
    paths, html, total = set(), [], 0
    for member in obj["assets"]:
        _need(type(member) is dict and set(member) == {"path", "sha256", "bytes", "mime"}, "asset_fields")
        name = asset_path(member["path"])
        _need(name.casefold() not in paths, "duplicate_asset_path")
        paths.add(name.casefold())
        _need(type(member["bytes"]) is int and 1 <= member["bytes"] <= MAX_FILE_BYTES, "asset_size_limit")
        total += member["bytes"]
        _need(total <= MAX_TOTAL_BYTES, "asset_total_limit")
        _need(isinstance(member["sha256"], str) and DIGEST.fullmatch(member["sha256"]), "asset_digest")
        _need(member["mime"] == MIMES[Path(name).suffix], "asset_mime")
        if member["mime"] == "text/html":
            html.append(name)
    _need(len(html) == 1 and obj["entry"] == html[0], "asset_entry")
    return obj


def build_id(manifest, schema_sha256):
    _need(isinstance(schema_sha256, str) and DIGEST.fullmatch(schema_sha256), "schema_digest")
    return _digest(canonical_bytes({"domain": "sys4ai-explorer-build-v1", "source_digest": manifest["source_digest"], "lock_sha256": manifest["lock_sha256"], "notices_sha256": manifest["notices_sha256"], "node": "25.9.0", "npm": manifest["toolchain"]["npm"], "api_version": 1, "schema_sha256": schema_sha256}))


def _reference(owner, value, members, *, expected=None):
    _need(isinstance(value, str) and value and not any(x in value for x in ("\\", "%", "?", "#", ":")) and not value.startswith("/"), "nonlocal_asset_import")
    # Generated relative references may use ./ or ../, but never escape assets.
    target = posixpath.normpath(posixpath.join(posixpath.dirname(owner), value))
    _need(target != ".." and not target.startswith("../"), "escaping_asset_import")
    asset_path(target)
    _need(target in members, "missing_asset_import")
    if expected:
        _need(members[target]["mime"] in expected, "import_mime")
    return target


class _HTMLImports(HTMLParser):
    def __init__(self, owner, members):
        super().__init__(convert_charrefs=True)
        self.refs = set()
        self.owner, self.members = owner, members
        self.script = False

    def reference(self, value, expected):
        self.refs.add(_reference(self.owner, value, self.members, expected=expected))

    def handle_starttag(self, tag, attrs):
        keys = [k for k, _ in attrs]
        _need(len(set(keys)) == len(keys), "duplicate_html_attribute")
        attrs = dict(attrs)
        _need(tag not in {"base", "iframe", "object", "embed", "style", "svg", "math"}, "active_html")
        _need(not any(k.startswith("on") or k in {"style", "srcset", "srcdoc", "action", "formaction", "ping", "poster", "background", "manifest"} for k in attrs), "active_html_attribute")
        if tag == "script":
            _need(attrs.get("type") == "module" and attrs.get("src") and not self.script, "inline_or_classic_script")
            self.reference(attrs["src"], {"text/javascript"})
            self.script = True
        elif "src" in attrs:
            raise AssetError("unsupported_html_resource")
        if tag == "link":
            rel = attrs.get("rel")
            _need(rel in {"stylesheet", "modulepreload"} and attrs.get("href"), "unsupported_html_link")
            self.reference(attrs["href"], {"text/css"} if rel == "stylesheet" else {"text/javascript"})
        elif "href" in attrs:
            _need(tag == "a" and attrs["href"].startswith("#"), "nonlocal_html_link")
        if tag == "meta":
            _need("http-equiv" not in attrs, "active_html_meta")

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        if tag == "script":
            self.script = False

    def handle_data(self, data):
        _need(not self.script or not data.strip(), "inline_script")


def _js_tokens(text):
    """Conservative lexer for bundled ESM import closure, not a JS interpreter.

    String escapes in import specifiers and computed imports are rejected. Scan
    template expressions too, so templates cannot hide a dynamic import.
    """
    n, i, previous = len(text), 0, None
    expression_start = {None, "(", "[", "{", "=", ":", ",", ";", "!", "?", "&&", "||", "return", "throw", "case", "=>"}
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if text.startswith("//", i):
            j = text.find("\n", i + 2)
            i = n if j < 0 else j + 1
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            _need(j >= 0, "invalid_js_comment")
            i = j + 2
            continue
        if ch in "\"'":
            quote, start, escaped = ch, i + 1, False
            i += 1
            while i < n and text[i] != quote:
                if text[i] == "\\":
                    escaped = True
                    i += 2
                else:
                    i += 1
            _need(i < n, "invalid_js_string")
            yield ("string", text[start:i], escaped)
            i += 1
            previous = "string"
            continue
        if ch == "`":
            start, dynamic, escaped = i + 1, False, False
            i += 1
            while i < n:
                if text[i] == "\\":
                    escaped = True
                    i += 2
                elif text[i] == "`":
                    if not dynamic:
                        yield ("string", text[start:i], escaped)
                    i += 1
                    break
                elif text.startswith("${", i):
                    j = _template_expression_end(text, i + 2)
                    if not dynamic:
                        yield ("dynamic_template", "template", escaped)
                        dynamic = True
                    yield from _js_tokens(text[i + 2:j])
                    i = j + 1
                else:
                    i += 1
            else:
                raise AssetError("invalid_js_template")
            previous = "string"
            continue
        if ch == "/" and previous in expression_start:
            i += 1
            in_class = False
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == "[":
                    in_class = True
                elif text[i] == "]":
                    in_class = False
                elif text[i] == "/" and not in_class:
                    i += 1
                    break
                i += 1
            else:
                raise AssetError("invalid_js_regex")
            while i < n and text[i].isalpha():
                i += 1
            previous = "regex"
            continue
        if ch.isalpha() or ch in "_$" or ord(ch) >= 128:
            start = i
            i += 1
            while i < n and (text[i].isalnum() or text[i] in "_$" or ord(text[i]) >= 128):
                i += 1
            previous = text[start:i]
            yield ("word", previous, False)
            continue
        _need(ch != "\\", "escaped_js_identifier")
        token = text[i:i + 2] if text[i:i + 2] in {"=>", "&&", "||"} else ch
        i += len(token)
        previous = token
        yield ("punct", token, False)


def _template_expression_end(text, start, nesting=0):
    _need(nesting <= 16, "js_template_depth")
    i, depth = start, 1
    while i < len(text):
        ch = text[i]
        if ch == "`":
            i += 1
            while i < len(text) and text[i] != "`":
                if text[i] == "\\":
                    i += 2
                elif text.startswith("${", i):
                    i = _template_expression_end(text, i + 2, nesting + 1) + 1
                else:
                    i += 1
            _need(i < len(text), "invalid_js_template")
        elif ch in "\"'":
            quote = ch
            i += 1
            while i < len(text) and text[i] != quote:
                i += 2 if text[i] == "\\" else 1
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            _need(j >= 0, "invalid_js_comment")
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i + 2)
            _need(j >= 0, "invalid_js_template")
            i = j
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise AssetError("invalid_js_template")


def _js_imports(text):
    tokens = iter(_js_tokens(text))
    pending = []
    def take():
        return pending.pop() if pending else next(tokens, None)
    previous = None
    while (current := take()) is not None:
        kind, value, escaped = current
        if value == "import" and kind == "word" and previous != ".":
            nxt = take()
            _need(nxt is not None, "invalid_js_import")
            if nxt[1] == ".":
                previous = "."
                continue
            if nxt[1] == "(":
                spec, end = take(), take()
                _need(spec is not None and spec[0] == "string" and not spec[2] and end is not None and end[1] == ")", "computed_js_import")
                yield spec[1]
            elif nxt[0] == "string":
                _need(not nxt[2], "escaped_js_import")
                yield nxt[1]
            else:
                while (token := take()) is not None:
                    _need(token[1] != ";", "invalid_js_import")
                    if token[1] == "from" and token[0] == "word":
                        spec = take()
                        _need(spec is not None and spec[0] == "string" and not spec[2], "invalid_js_import")
                        yield spec[1]
                        break
                else:
                    raise AssetError("invalid_js_import")
        elif value == "export" and kind == "word" and previous != ".":
            nxt = take()
            if nxt and nxt[1] in {"*", "{"}:
                if nxt[1] == "{":
                    depth = 1
                    while depth:
                        token = take()
                        _need(token is not None, "invalid_js_export")
                        depth += int(token[1] == "{") - int(token[1] == "}")
                    nxt = take()
                else:
                    nxt = take()
                    if nxt and nxt[1] == "as":
                        _need(take() is not None, "invalid_js_export")
                        nxt = take()
                if nxt and nxt[0] == "word" and nxt[1] == "from":
                    spec = take()
                    _need(spec is not None and spec[0] == "string" and not spec[2], "invalid_js_import")
                    yield spec[1]
                elif nxt:
                    pending.append(nxt)
            elif nxt:
                pending.append(nxt)
        previous = value


def _css_imports(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    # Escaped CSS keywords could conceal url/import. Bundle CSS needs no escaped
    # identifiers; reject them, while ordinary non-ASCII text remains permitted.
    _need("\\" not in text, "escaped_css_syntax")
    _need(not re.search(r"(?:-webkit-)?image-set\s*\(", text, re.I), "unsupported_css_image_resource")
    pattern = r"@import\s+(?:url\(\s*)?([\"'])(.*?)\1\s*\)?|url\(\s*(?:([\"'])(.*?)\3|([^()\s]+))\s*\)"
    for match in re.finditer(pattern, text, flags=re.I | re.S):
        yield match.group(2) if match.group(1) else match.group(4) if match.group(3) else match.group(5)
    # Unparsed import/url forms must fail rather than evade the member check.
    residual = re.sub(pattern, "", text, flags=re.I | re.S)
    _need(not re.search(r"@import\b|\burl\s*\(", residual, re.I), "invalid_css_import")


def validate_closure(manifest, bodies):
    members = {m["path"]: m for m in manifest["assets"]}
    _need(set(bodies) == set(members), "asset_inventory")
    graph = {}
    for path, member in members.items():
        try:
            text = bodies[path].decode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise AssetError("invalid_asset_utf8") from exc
        _need("sourceMappingURL" not in text and "@vite/client" not in text, "development_asset")
        refs = []
        if member["mime"] == "text/html":
            parser = _HTMLImports(path, members)
            parser.feed(text)
            parser.close()
            _need(not parser.script, "unclosed_html_script")
            graph[path] = sorted(parser.refs)
            continue
        if member["mime"] == "text/javascript":
            refs = ((v, {"text/javascript"}) for v in _js_imports(text))
        else:
            refs = ((v, {"text/css"}) for v in _css_imports(text))
        # Repeated references do not allocate an unbounded edge list: a closed
        # package has at most MAX_FILES distinct targets per member.
        graph[path] = sorted({_reference(path, v, members, expected=mime) for v, mime in refs})
    visited, queue = set(), [manifest["entry"]]
    while queue:
        path = queue.pop()
        if path not in visited:
            visited.add(path)
            queue.extend(graph[path])
    _need(visited == set(members), "unreachable_asset")
    return graph


@dataclass(frozen=True)
class AssetPackage:
    root: Path
    manifest_bytes: bytes
    manifest_sha256: str
    manifest: object
    members: object
    root_identity: tuple

    def read(self, target):
        return read_asset(self, target)


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def load_assets(root, *, schema_sha256=None, lock_path=None, notices_path=None):
    """Validate a bounded closed package. Optional exact metadata binds build ID."""
    try:
        root = Path(root).absolute()
        fd = directory_fd(root)
        try:
            root_stat = os.fstat(fd)
            raw = _read_at(fd, "manifest.json", MAX_MANIFEST_BYTES)
            manifest = validate_manifest(raw)
            if schema_sha256 is not None:
                _need(build_id(manifest, schema_sha256) == manifest["build_id"], "build_identity")
            for source, key in ((lock_path, "lock_sha256"), (notices_path, "notices_sha256")):
                if source is not None:
                    _need(_digest(read_regular(source, MAX_FILE_BYTES)) == manifest[key], "package_metadata_digest")
            bodies = {}
            for member in manifest["assets"]:
                data = _read_at(fd, member["path"], member["bytes"])
                _need(len(data) == member["bytes"] and _digest(data) == member["sha256"], "asset_hash_mismatch")
                bodies[member["path"]] = data
            validate_closure(manifest, bodies)
            _need(_read_at(fd, "manifest.json", MAX_MANIFEST_BYTES) == raw, "manifest_changed_during_read")
            current = os.stat(root, follow_symlinks=False)
            _need((current.st_dev, current.st_ino) == (root_stat.st_dev, root_stat.st_ino), "package_directory_changed")
            return AssetPackage(root, raw, _digest(raw), _freeze(manifest), _freeze({m["path"]: m for m in manifest["assets"]}), (root_stat.st_dev, root_stat.st_ino))
        finally:
            os.close(fd)
    except OSError as exc:
        raise AssetError("asset_unavailable") from exc


def read_asset(package, target):
    """Return (bytes, MIME) for an exact HTTP path; never decode path aliases."""
    if not isinstance(target, str) or not target.startswith("/") or any(c in target for c in ("%", "?", "#", "\\")):
        raise AssetError("unmanifested_resource", "resource_forbidden")
    path = package.manifest["entry"] if target in {"/", "/index.html"} else target[1:]
    if path not in package.members:
        raise AssetError("unmanifested_resource", "resource_forbidden")
    try:
        fd = directory_fd(package.root)
        try:
            st = os.fstat(fd)
            _need((st.st_dev, st.st_ino) == package.root_identity, "package_directory_changed")
            _need(_read_at(fd, "manifest.json", MAX_MANIFEST_BYTES) == package.manifest_bytes, "manifest_changed")
            member = package.members[path]
            data = _read_at(fd, path, member["bytes"])
            _need(len(data) == member["bytes"] and _digest(data) == member["sha256"], "asset_hash_mismatch")
            _need(_read_at(fd, "manifest.json", MAX_MANIFEST_BYTES) == package.manifest_bytes, "manifest_changed")
            return data, member["mime"]
        finally:
            os.close(fd)
    except OSError as exc:
        raise AssetError("asset_unavailable") from exc
