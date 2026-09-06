"""Deterministic, format-aware normalization for the base profile."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import re
import tomllib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, cast

import yaml
from pydantic import JsonValue
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from sys4ai_memory.contracts import (
    API_VERSION,
    SCHEMA_VERSION,
    CoreRecordType,
    EpistemicStatus,
    ErrorCategory,
    RecordStatus,
)
from sys4ai_memory.contracts.models import (
    AuthorityBinding,
    EpistemicMetadata,
    IndexingMetadata,
    LifecycleMetadata,
    MemoryContent,
    MemoryRecord,
    ProcessingMetadata,
    SecurityMetadata,
    SourceAnchor,
    SourceRecord,
)
from sys4ai_memory.util.ids import stable_id
from sys4ai_memory.util.paths import PathBoundaryError, resolve_within
from sys4ai_memory.util.time import ensure_utc, utc_now

from .models import IngestionBatchResult, IngestionFailure, NormalizedDocument

ADAPTER_VERSION = "1.0.0"
DEFAULT_PROFILE_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class _Unit:
    title: str
    exact: str
    locator: dict[str, JsonValue]
    structured: dict[str, JsonValue]
    record_type: str = CoreRecordType.SOURCE_FRAGMENT.value
    lifecycle_status: RecordStatus = RecordStatus.ACTIVE
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    profile_type: str | None = None
    indexing: IndexingMetadata | None = None


@dataclass(frozen=True, slots=True)
class OptionalAdapterUnit:
    """Provider-neutral unit returned by an explicitly supplied format adapter."""

    title: str
    exact: str
    locator: dict[str, JsonValue]
    structured: dict[str, JsonValue]
    record_type: str = CoreRecordType.SOURCE_FRAGMENT.value
    profile_type: str | None = None
    lifecycle_status: RecordStatus = RecordStatus.ACTIVE
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    indexing: IndexingMetadata | None = None

    def __post_init__(self) -> None:
        if not self.title.strip() or not self.exact.strip() or not self.locator:
            raise ValueError("optional adapter units require title, exact text, and locator")
        core_types = {item.value for item in CoreRecordType}
        if self.record_type not in core_types and not self.profile_type:
            raise ValueError("optional extension records require profile_type")
        if (
            self.valid_from is not None
            and self.valid_to is not None
            and ensure_utc(self.valid_to) < ensure_utc(self.valid_from)
        ):
            raise ValueError("optional adapter valid_to precedes valid_from")


class OptionalSourceAdapter(Protocol):
    """Explicit byte-oriented seam for non-base and domain source formats."""

    adapter_id: str
    adapter_version: str
    formats: frozenset[str]

    def units(
        self,
        raw_bytes: bytes,
        source: SourceRecord,
    ) -> tuple[OptionalAdapterUnit, ...]: ...


class _Adapter(Protocol):
    adapter_id: str
    formats: frozenset[str]

    def units(self, text: str, path: str) -> tuple[_Unit, ...]: ...


class _AdapterParseError(ValueError):
    pass


def _json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, bool, int)):
        return cast(JsonValue, value)
    if isinstance(value, float):
        if value != value or value in {float("inf"), float("-inf")}:
            return cast(JsonValue, str(value))
        return cast(JsonValue, value)
    if isinstance(value, datetime):
        return cast(JsonValue, value.isoformat())
    if isinstance(value, Mapping):
        return cast(
            JsonValue,
            {str(key): _json_value(item) for key, item in value.items()},
        )
    if isinstance(value, (list, tuple)):
        return cast(JsonValue, [_json_value(item) for item in value])
    return cast(JsonValue, str(value))


def _json_object(value: Mapping[object, object]) -> dict[str, JsonValue]:
    return {str(key): _json_value(item) for key, item in value.items()}


def _line_locator(label: str, start: int, end: int) -> dict[str, JsonValue]:
    return {"label": label, "line_start": start, "line_end": end}


def _plain_heading(value: str) -> str:
    value = re.sub(r"\s+#+\s*$", "", value.strip())
    return re.sub(r"[`*_]", "", value).strip()


class MarkdownAdapter:
    adapter_id = "markdown"
    formats = frozenset({"markdown"})
    _heading = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
    _table_separator = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$")

    def units(self, text: str, path: str) -> tuple[_Unit, ...]:
        del path
        lines = text.splitlines(keepends=True)
        headings: list[tuple[int, int, str]] = []
        in_fence = False
        for index, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            match = self._heading.match(line.rstrip("\r\n"))
            if match:
                headings.append((index, len(match.group(1)), _plain_heading(match.group(2))))

        units: list[_Unit] = []
        if headings and any(line.strip() for line in lines[: headings[0][0]]):
            exact = "".join(lines[: headings[0][0]])
            units.append(
                _Unit(
                    title="Document preamble",
                    exact=exact,
                    locator=_line_locator("preamble", 1, headings[0][0]),
                    structured={"unit_kind": "preamble"},
                )
            )
        for position, (start, level, title) in enumerate(headings):
            end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
            exact = "".join(lines[start:end])
            record_type = (
                CoreRecordType.REQUIREMENT.value
                if re.search(r"\b(?:requirement|MEM-FR-|REQ[-_])", title, re.IGNORECASE)
                else CoreRecordType.SOURCE_FRAGMENT.value
            )
            units.append(
                _Unit(
                    title=title,
                    exact=exact,
                    locator=_line_locator(f"heading: {title}", start + 1, end),
                    structured={
                        "unit_kind": "heading",
                        "heading": title,
                        "heading_level": level,
                    },
                    record_type=record_type,
                )
            )

        # Markdown tables are natural units of their own.  They coexist with
        # heading blocks so exact row anchors do not depend on large sections.
        index = 0
        while index + 1 < len(lines):
            header_line = lines[index].rstrip("\r\n")
            separator = lines[index + 1].rstrip("\r\n")
            if "|" not in header_line or not self._table_separator.match(separator):
                index += 1
                continue
            headers = _markdown_cells(header_line)
            row_index = index + 2
            while row_index < len(lines) and "|" in lines[row_index]:
                exact = lines[row_index]
                if not exact.strip():
                    break
                cells = _markdown_cells(exact.rstrip("\r\n"))
                if len(cells) != len(headers):
                    break
                values = dict(zip(headers, cells, strict=True))
                identity = cells[0] if cells else f"line-{row_index + 1}"
                record_type = (
                    CoreRecordType.REQUIREMENT.value
                    if re.match(r"^(?:MEM-FR-|REQ[-_])", identity, re.IGNORECASE)
                    else CoreRecordType.SOURCE_FRAGMENT.value
                )
                units.append(
                    _Unit(
                        title=identity,
                        exact=exact,
                        locator=_line_locator(
                            f"table row: {headers[0]}={identity}", row_index + 1, row_index + 1
                        ),
                        structured={
                            "unit_kind": "table_row",
                            "fields": cast(JsonValue, values),
                        },
                        record_type=record_type,
                    )
                )
                row_index += 1
            index = max(index + 1, row_index)

        if not units and text.strip():
            units.append(
                _Unit(
                    title="Markdown document",
                    exact=text,
                    locator=_line_locator("document body", 1, max(1, len(lines))),
                    structured={"unit_kind": "document_body"},
                )
            )
        return tuple(units)


def _markdown_cells(line: str) -> list[str]:
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [cell.strip().strip("`") for cell in value.split("|")]


class YamlAdapter:
    adapter_id = "yaml"
    formats = frozenset({"yaml"})

    def units(self, text: str, path: str) -> tuple[_Unit, ...]:
        del path
        try:
            root = yaml.compose(text, Loader=yaml.SafeLoader)
        except yaml.YAMLError as error:
            raise _AdapterParseError("YAML syntax validation failed") from error
        if root is None:
            return ()
        units: list[_Unit] = []
        self._walk(root, text, (), units, depth=0, active=set())
        return tuple(units)

    def _walk(
        self,
        node: Node,
        text: str,
        parts: tuple[str, ...],
        units: list[_Unit],
        *,
        depth: int,
        active: set[int],
    ) -> None:
        if depth > 64:
            raise _AdapterParseError("YAML nesting exceeds 64 levels")
        identity = id(node)
        if identity in active:
            raise _AdapterParseError("recursive YAML aliases are not supported")
        active.add(identity)
        try:
            if isinstance(node, MappingNode):
                for key_node, value_node in node.value:
                    if not isinstance(key_node, ScalarNode):
                        raise _AdapterParseError("YAML mapping keys must be scalar")
                    key = key_node.value
                    child_parts = (*parts, key)
                    dotted = ".".join(child_parts)
                    exact = text[key_node.start_mark.index : value_node.end_mark.index]
                    if exact.strip():
                        units.append(
                            _Unit(
                                title=key,
                                exact=exact,
                                locator=_line_locator(
                                    f"key: {dotted}",
                                    key_node.start_mark.line + 1,
                                    value_node.end_mark.line + 1,
                                ),
                                structured={
                                    "unit_kind": "mapping_entry",
                                    "key": dotted,
                                    "value": _yaml_node_value(value_node, depth=depth + 1),
                                },
                                record_type=_record_type_for_identity(key),
                            )
                        )
                    self._walk(
                        value_node,
                        text,
                        child_parts,
                        units,
                        depth=depth + 1,
                        active=active,
                    )
            elif isinstance(node, SequenceNode):
                for index, value_node in enumerate(node.value):
                    child_parts = (*parts, str(index))
                    label = ".".join(parts) + f"[{index}]"
                    exact = text[value_node.start_mark.index : value_node.end_mark.index]
                    if exact.strip():
                        units.append(
                            _Unit(
                                title=label,
                                exact=exact,
                                locator=_line_locator(
                                    f"key: {label}",
                                    value_node.start_mark.line + 1,
                                    value_node.end_mark.line + 1,
                                ),
                                structured={
                                    "unit_kind": "sequence_item",
                                    "key": label,
                                    "value": _yaml_node_value(value_node, depth=depth + 1),
                                },
                            )
                        )
                    self._walk(
                        value_node,
                        text,
                        child_parts,
                        units,
                        depth=depth + 1,
                        active=active,
                    )
        finally:
            active.remove(identity)


def _yaml_node_value(node: Node, *, depth: int) -> JsonValue:
    if depth > 64:
        raise _AdapterParseError("YAML nesting exceeds 64 levels")
    if isinstance(node, ScalarNode):
        tag = node.tag
        value = cast(str, node.value)
        if tag.endswith(":null"):
            return None
        if tag.endswith(":bool"):
            return value.casefold() in {"true", "yes", "on"}
        if tag.endswith(":int"):
            try:
                return int(value, 0)
            except ValueError:
                return value
        if tag.endswith(":float"):
            try:
                return float(value)
            except ValueError:
                return value
        return value
    if isinstance(node, SequenceNode):
        return cast(JsonValue, [_yaml_node_value(item, depth=depth + 1) for item in node.value])
    if isinstance(node, MappingNode):
        result: dict[str, JsonValue] = {}
        for key, value in node.value:
            if not isinstance(key, ScalarNode):
                raise _AdapterParseError("YAML mapping keys must be scalar")
            result[key.value] = _yaml_node_value(value, depth=depth + 1)
        return cast(JsonValue, result)
    raise _AdapterParseError("unsupported YAML node")


class CsvAdapter:
    adapter_id = "csv"
    formats = frozenset({"csv"})

    def units(self, text: str, path: str) -> tuple[_Unit, ...]:
        del path
        lines = text.splitlines(keepends=True)
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        try:
            headers = next(reader)
        except StopIteration:
            return ()
        except csv.Error as error:
            raise _AdapterParseError("CSV syntax validation failed") from error
        if (
            not headers
            or any(not header for header in headers)
            or len(headers) != len(set(headers))
        ):
            raise _AdapterParseError("CSV headers must be nonblank and unique")
        previous_line = reader.line_num
        units: list[_Unit] = []
        try:
            for row in reader:
                end_line = reader.line_num
                start_line = previous_line + 1
                previous_line = end_line
                if not row and start_line == end_line:
                    continue
                if len(row) != len(headers):
                    raise _AdapterParseError("CSV row has the wrong column count")
                exact = "".join(lines[start_line - 1 : end_line])
                values = dict(zip(headers, row, strict=True))
                identity = row[0] or f"line-{start_line}"
                units.append(
                    _Unit(
                        title=identity,
                        exact=exact,
                        locator=_line_locator(
                            f"row: {headers[0]}={identity}", start_line, end_line
                        ),
                        structured={
                            "unit_kind": "csv_row",
                            "fields": cast(JsonValue, values),
                        },
                        record_type=_record_type_for_identity(identity),
                    )
                )
        except csv.Error as error:
            raise _AdapterParseError("CSV syntax validation failed") from error
        return tuple(units)


class TomlAdapter:
    adapter_id = "toml"
    formats = frozenset({"toml"})
    _section = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")
    _key = re.compile(r"^\s*([A-Za-z0-9_-]+)\s*=")

    def units(self, text: str, path: str) -> tuple[_Unit, ...]:
        del path
        try:
            parsed = tomllib.loads(text)
        except tomllib.TOMLDecodeError as error:
            raise _AdapterParseError("TOML syntax validation failed") from error
        lines = text.splitlines(keepends=True)
        section_starts: list[tuple[int, tuple[str, ...]]] = []
        for index, line in enumerate(lines):
            match = self._section.match(line.rstrip("\r\n"))
            if match:
                section_starts.append(
                    (index, tuple(part.strip() for part in match.group(1).split(".")))
                )

        units: list[_Unit] = []
        for position, (start, parts) in enumerate(section_starts):
            end = (
                section_starts[position + 1][0]
                if position + 1 < len(section_starts)
                else len(lines)
            )
            label = ".".join(parts)
            value = _mapping_path(parsed, parts)
            units.append(
                _Unit(
                    title=label,
                    exact="".join(lines[start:end]),
                    locator=_line_locator(f"section: {label}", start + 1, end),
                    structured={
                        "unit_kind": "configuration_section",
                        "section": label,
                        "value": _json_value(value),
                    },
                )
            )

        active_parts: tuple[str, ...] = ()
        for index, line in enumerate(lines):
            section_match = self._section.match(line.rstrip("\r\n"))
            if section_match:
                active_parts = tuple(part.strip() for part in section_match.group(1).split("."))
                continue
            key_match = self._key.match(line)
            if not key_match:
                continue
            key = key_match.group(1)
            parts = (*active_parts, key)
            dotted = ".".join(parts)
            units.append(
                _Unit(
                    title=key,
                    exact=line,
                    locator=_line_locator(f"key: {dotted}", index + 1, index + 1),
                    structured={
                        "unit_kind": "configuration_key",
                        "key": dotted,
                        "value": _json_value(_mapping_path(parsed, parts)),
                    },
                )
            )
        return tuple(units)


def _mapping_path(value: Mapping[str, Any], parts: tuple[str, ...]) -> object:
    current: object = value
    for part in parts:
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


class JsonAdapter:
    adapter_id = "json"
    formats = frozenset({"json"})

    def units(self, text: str, path: str) -> tuple[_Unit, ...]:
        del path
        value = _load_json(text)
        units: list[_Unit] = []
        self._walk(value, (), units, depth=0)
        return tuple(units)

    def _walk(
        self,
        value: object,
        parts: tuple[str, ...],
        units: list[_Unit],
        *,
        depth: int,
    ) -> None:
        if depth > 64:
            raise _AdapterParseError("JSON nesting exceeds 64 levels")
        if isinstance(value, dict):
            if parts and _mapping_identity(value)[0] is not None:
                # The containing object is the natural record. Its scalar
                # children remain structured fields and inherit its lifecycle.
                return
            for key, child in value.items():
                child_parts = (*parts, str(key))
                pointer = _json_pointer(child_parts)
                if not isinstance(child, list):
                    units.append(_json_unit(child, pointer))
                self._walk(child, child_parts, units, depth=depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                child_parts = (*parts, str(index))
                pointer = _json_pointer(child_parts)
                units.append(_json_unit(child, pointer))
                self._walk(child, child_parts, units, depth=depth + 1)


class JsonSchemaAdapter(JsonAdapter):
    adapter_id = "json_schema"
    formats = frozenset({"json_schema"})

    def units(self, text: str, path: str) -> tuple[_Unit, ...]:
        units = list(super().units(text, path))
        value = _load_json(text)
        if not isinstance(value, dict):
            raise _AdapterParseError("JSON Schema root must be an object")
        properties = value.get("properties")
        if isinstance(properties, dict):
            for name, definition in properties.items():
                pointer = _json_pointer(("properties", str(name)))
                unit = _json_unit(definition, pointer)
                units.append(
                    replace(
                        unit,
                        title=str(name),
                        locator={"label": f"schema key: {pointer}", "json_pointer": pointer},
                        structured={
                            "unit_kind": "schema_definition",
                            "schema_key": str(name),
                            "json_pointer": pointer,
                            "value": _json_value(definition),
                        },
                    )
                )
        return tuple(units)


def _load_json(text: str) -> object:
    def reject_constant(value: str) -> object:
        raise ValueError(f"non-JSON numeric constant {value}")

    try:
        return json.loads(text, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError) as error:
        raise _AdapterParseError("JSON syntax validation failed") from error


def _json_pointer(parts: tuple[str, ...]) -> str:
    escaped = (part.replace("~", "~0").replace("/", "~1") for part in parts)
    return "/" + "/".join(escaped)


def _json_unit(value: object, pointer: str) -> _Unit:
    if isinstance(value, Mapping):
        structured_value = _json_object(value)
        title = _mapping_title(value, pointer)
        record_type = _record_type_for_mapping(value)
        lifecycle, valid_from, valid_to = _lifecycle_for_mapping(value)
    else:
        structured_value = {"value": _json_value(value)}
        title = pointer.rsplit("/", 1)[-1] or "root"
        record_type = CoreRecordType.SOURCE_FRAGMENT.value
        lifecycle, valid_from, valid_to = RecordStatus.ACTIVE, None, None
    exact = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _Unit(
        title=title,
        exact=exact,
        locator={"label": f"json-pointer: {pointer}", "json_pointer": pointer},
        structured={
            "unit_kind": "json_value",
            "json_pointer": pointer,
            **structured_value,
        },
        record_type=record_type,
        lifecycle_status=lifecycle,
        valid_from=valid_from,
        valid_to=valid_to,
    )


class JsonLinesAdapter:
    adapter_id = "jsonl"
    formats = frozenset({"jsonl"})

    def units(self, text: str, path: str) -> tuple[_Unit, ...]:
        del path
        units: list[_Unit] = []
        for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
            if not line.strip():
                continue
            value = _load_json(line)
            if not isinstance(value, dict):
                raise _AdapterParseError("JSONL rows must be JSON objects")
            identity_key, identity_value = _mapping_identity(value)
            label = (
                f"{identity_key}: {identity_value}"
                if identity_key is not None
                else f"line: {line_number}"
            )
            lifecycle, valid_from, valid_to = _lifecycle_for_mapping(value)
            units.append(
                _Unit(
                    title=str(identity_value) if identity_value is not None else label,
                    exact=line,
                    locator=_line_locator(label, line_number, line_number),
                    structured={
                        "unit_kind": "jsonl_record",
                        "fields": cast(JsonValue, _json_object(value)),
                    },
                    record_type=_record_type_for_mapping(value),
                    lifecycle_status=lifecycle,
                    valid_from=valid_from,
                    valid_to=valid_to,
                )
            )
        return tuple(units)


class TextAdapter:
    adapter_id = "text"
    formats = frozenset({"text"})

    def units(self, text: str, path: str) -> tuple[_Unit, ...]:
        del path
        lines = text.splitlines(keepends=True)
        units: list[_Unit] = []
        start: int | None = None
        for index in range(len(lines) + 1):
            blank = index == len(lines) or not lines[index].strip()
            if start is None and not blank:
                start = index
            if start is None or not blank:
                continue
            exact = "".join(lines[start:index])
            title_line = next((line.strip() for line in lines[start:index] if line.strip()), "Text")
            units.append(
                _Unit(
                    title=title_line[:100],
                    exact=exact,
                    locator=_line_locator(f"paragraph: {len(units) + 1}", start + 1, index),
                    structured={"unit_kind": "paragraph", "paragraph": len(units) + 1},
                )
            )
            start = None
        return tuple(units)


class _PythonUnitCollector(ast.NodeVisitor):
    """Collect stable qualified Python symbols without indexing local variables."""

    def __init__(self, lines: list[str]) -> None:
        self._lines = lines
        self._scope: list[tuple[str, str]] = []
        self.units: list[_Unit] = []

    def _qualified(self, name: str) -> str:
        return ".".join((*[item[0] for item in self._scope], name))

    def _emit(self, node: ast.AST, name: str, kind: str) -> None:
        if not hasattr(node, "lineno"):
            return
        start = node.lineno
        end = getattr(node, "end_lineno", start) or start
        qualified = self._qualified(name)
        self.units.append(
            _Unit(
                title=qualified,
                exact="".join(self._lines[start - 1 : end]),
                locator=_line_locator(f"symbol: {qualified}", start, end),
                structured={
                    "unit_kind": "code_symbol",
                    "symbol": name,
                    "qualified_symbol": qualified,
                    "symbol_kind": kind,
                    "language": "python",
                },
            )
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._emit(node, node.name, "class")
        self._scope.append((node.name, "class"))
        self.generic_visit(node)
        self._scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._emit(node, node.name, "function")
        self._scope.append((node.name, "function"))
        self.generic_visit(node)
        self._scope.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        if not any(kind == "function" for _, kind in self._scope):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self._emit(node, target.id, "assignment")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if not any(kind == "function" for _, kind in self._scope) and isinstance(
            node.target, ast.Name
        ):
            self._emit(node, node.target.id, "assignment")
        self.generic_visit(node)


class PythonAdapter:
    adapter_id = "python"
    formats = frozenset({"python", "source_code"})

    def units(self, text: str, path: str) -> tuple[_Unit, ...]:
        del path
        try:
            tree = ast.parse(text)
        except SyntaxError as error:
            raise _AdapterParseError("Python syntax validation failed") from error
        lines = text.splitlines(keepends=True)
        collector = _PythonUnitCollector(lines)
        collector.visit(tree)
        units = collector.units
        units.sort(
            key=lambda item: (
                int(cast(int, item.locator.get("line_start", 0))),
                item.title,
            )
        )
        return tuple(units)


class GenericCodeAdapter:
    adapter_id = "source_code"
    formats = frozenset(
        {"source_code", "javascript", "typescript", "rust", "go", "java", "c", "cpp", "shell"}
    )
    _patterns = (
        ("class", re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)")),
        ("function", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)")),
        ("function", re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)")),
        ("function", re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)")),
        ("type", re.compile(r"^\s*(?:pub\s+)?(?:struct|enum|trait)\s+([A-Za-z_][A-Za-z0-9_]*)")),
        ("assignment", re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)")),
        ("function", re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{")),
    )

    def units(self, text: str, path: str) -> tuple[_Unit, ...]:
        suffix = Path(path).suffix.casefold().lstrip(".") or "source"
        units: list[_Unit] = []
        for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
            for kind, pattern in self._patterns:
                match = pattern.match(line)
                if match:
                    name = match.group(1)
                    units.append(
                        _Unit(
                            title=name,
                            exact=line,
                            locator=_line_locator(f"symbol: {name}", line_number, line_number),
                            structured={
                                "unit_kind": "code_symbol",
                                "symbol": name,
                                "symbol_kind": kind,
                                "language": suffix,
                            },
                        )
                    )
                    break
        return tuple(units)


_ADAPTERS: tuple[_Adapter, ...] = (
    MarkdownAdapter(),
    YamlAdapter(),
    CsvAdapter(),
    TomlAdapter(),
    JsonSchemaAdapter(),
    JsonAdapter(),
    JsonLinesAdapter(),
    TextAdapter(),
    PythonAdapter(),
    GenericCodeAdapter(),
)


def _optional_adapter_map(
    adapters: Iterable[OptionalSourceAdapter],
) -> dict[str, OptionalSourceAdapter]:
    base_ids = {adapter.adapter_id for adapter in _ADAPTERS}
    registered: dict[str, OptionalSourceAdapter] = {}
    for adapter in adapters:
        adapter_id = adapter.adapter_id
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:@-]*", adapter_id):
            raise ValueError("optional adapter ID is invalid")
        if adapter_id in base_ids:
            raise ValueError("optional adapters cannot replace a base adapter")
        if adapter_id in registered:
            raise ValueError("optional adapter IDs must be unique")
        if not re.fullmatch(
            r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
            r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?",
            adapter.adapter_version,
        ):
            raise ValueError("optional adapter version must be semantic version")
        if not adapter.formats or "any" in adapter.formats:
            raise ValueError("optional adapters require explicit non-any formats")
        if any(not value.strip() for value in adapter.formats):
            raise ValueError("optional adapter formats must not be blank")
        registered[adapter_id] = adapter
    return registered


def available_adapters(
    optional_adapters: Iterable[OptionalSourceAdapter] = (),
) -> tuple[str, ...]:
    optional = _optional_adapter_map(optional_adapters)
    return (*tuple(adapter.adapter_id for adapter in _ADAPTERS), *tuple(sorted(optional)))


def _select_optional_adapter(
    source: SourceRecord,
    optional_adapters: Iterable[OptionalSourceAdapter],
) -> OptionalSourceAdapter | None:
    registered = _optional_adapter_map(optional_adapters)
    adapter = registered.get(source.ingestion_adapter)
    if adapter is None:
        return None
    if source.format not in adapter.formats:
        raise IngestionFailure(
            source_id=source.source_id,
            adapter=source.ingestion_adapter,
            stage="adapter_selection",
            category=ErrorCategory.INGESTION_FAILED,
            message="optional adapter does not support the declared source format",
            recovery_action="correct the profile adapter declaration and repeat ingestion",
        )
    return adapter


def _select_adapter(source: SourceRecord, path: str) -> _Adapter:
    requested = source.ingestion_adapter
    format_name = source.format
    if format_name == "source_code" and Path(path).suffix.casefold() in {".py", ".pyi"}:
        return next(adapter for adapter in _ADAPTERS if adapter.adapter_id == "python")
    for adapter in _ADAPTERS:
        if requested == adapter.adapter_id and format_name in adapter.formats:
            return adapter
    for adapter in _ADAPTERS:
        if format_name in adapter.formats:
            return adapter
    raise IngestionFailure(
        source_id=source.source_id,
        adapter=requested,
        stage="adapter_selection",
        category=ErrorCategory.INGESTION_FAILED,
        message="no deterministic base-profile adapter supports the declared format",
        recovery_action="register a supported format adapter or correct the source declaration",
    )


def normalize_source(
    project_root: Path,
    source: SourceRecord,
    *,
    processed_at: datetime | None = None,
    profile_version: str = DEFAULT_PROFILE_VERSION,
    max_file_bytes: int = 8 * 1024 * 1024,
    max_chunk_chars: int = 64 * 1024,
    optional_adapters: Iterable[OptionalSourceAdapter] = (),
) -> NormalizedDocument:
    """Safely read and normalize one repository source."""

    if source.origin_uri is not None:
        raise IngestionFailure(
            source_id=source.source_id,
            adapter=source.ingestion_adapter,
            stage="source_read",
            category=ErrorCategory.INGESTION_FAILED,
            message="external source bytes must be supplied explicitly",
            recovery_action="use normalize_bytes with the registered external content",
        )
    try:
        path = resolve_within(project_root, source.path_or_uri)
    except PathBoundaryError as error:
        raise IngestionFailure(
            source_id=source.source_id,
            adapter=source.ingestion_adapter,
            stage="source_read",
            category=ErrorCategory.SOURCE_EXCLUDED,
            message="source path failed the project-root boundary check",
            recovery_action="correct the registered path and repeat discovery",
        ) from error
    try:
        if path.stat().st_size > max_file_bytes:
            raise IngestionFailure(
                source_id=source.source_id,
                adapter=source.ingestion_adapter,
                stage="source_read",
                category=ErrorCategory.INGESTION_FAILED,
                message="source exceeds the configured byte limit",
                recovery_action="use an approved bounded adapter or reduce the source size",
            )
        with path.open("rb") as stream:
            raw_bytes = stream.read(max_file_bytes + 1)
    except OSError as error:
        raise IngestionFailure(
            source_id=source.source_id,
            adapter=source.ingestion_adapter,
            stage="source_read",
            category=ErrorCategory.INGESTION_FAILED,
            message="source could not be read",
            recovery_action="restore the source or rerun discovery to reconcile it",
        ) from error
    return normalize_bytes(
        source,
        raw_bytes,
        processed_at=processed_at,
        profile_version=profile_version,
        max_file_bytes=max_file_bytes,
        max_chunk_chars=max_chunk_chars,
        optional_adapters=optional_adapters,
    )


def normalize_bytes(
    source: SourceRecord,
    raw_bytes: bytes,
    *,
    processed_at: datetime | None = None,
    profile_version: str = DEFAULT_PROFILE_VERSION,
    max_file_bytes: int = 8 * 1024 * 1024,
    max_chunk_chars: int = 64 * 1024,
    optional_adapters: Iterable[OptionalSourceAdapter] = (),
) -> NormalizedDocument:
    """Normalize already authorized bytes without a provider or model call."""

    if len(raw_bytes) > max_file_bytes:
        raise IngestionFailure(
            source_id=source.source_id,
            adapter=source.ingestion_adapter,
            stage="source_read",
            category=ErrorCategory.INGESTION_FAILED,
            message="source exceeds the configured byte limit",
            recovery_action="use an approved bounded adapter or reduce the source size",
        )
    if max_chunk_chars <= 0:
        raise ValueError("max_chunk_chars must be positive")
    digest = hashlib.sha256(raw_bytes).hexdigest()
    if source.content_sha256 != digest:
        raise IngestionFailure(
            source_id=source.source_id,
            adapter=source.ingestion_adapter,
            stage="integrity_check",
            category=ErrorCategory.INDEX_DRIFT,
            message="source bytes do not match the discovered content hash",
            recovery_action="repeat safe discovery before ingestion",
        )
    optional_adapter = _select_optional_adapter(source, optional_adapters)
    if optional_adapter is not None:
        return _normalize_optional_bytes(
            source,
            raw_bytes,
            optional_adapter,
            processed_at=processed_at,
            profile_version=profile_version,
            max_chunk_chars=max_chunk_chars,
        )
    adapter = _select_adapter(source, source.path_or_uri)
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise IngestionFailure(
            source_id=source.source_id,
            adapter=source.ingestion_adapter,
            stage="decode",
            category=ErrorCategory.INGESTION_FAILED,
            message="base-profile text sources must be valid UTF-8",
            recovery_action="use an approved format adapter with explicit encoding handling",
        ) from error
    if not text.strip():
        raise IngestionFailure(
            source_id=source.source_id,
            adapter=source.ingestion_adapter,
            stage="parse",
            category=ErrorCategory.INGESTION_FAILED,
            message="empty sources do not produce durable records",
            recovery_action="remove the empty registration or add source content",
        )
    timestamp = ensure_utc(processed_at) if processed_at is not None else utc_now()
    try:
        natural_units = adapter.units(text, source.path_or_uri)
    except IngestionFailure:
        raise
    except _AdapterParseError as error:
        raise IngestionFailure(
            source_id=source.source_id,
            adapter=adapter.adapter_id,
            stage="parse",
            category=ErrorCategory.INGESTION_FAILED,
            message=str(error),
            recovery_action="correct the source syntax and resume from the source checkpoint",
        ) from error
    bounded_units = tuple(
        split
        for unit in natural_units
        for split in _bounded_unit(unit, max_chunk_chars=max_chunk_chars)
    )
    artifact_unit = _Unit(
        title=source.path_or_uri,
        exact=text,
        locator={"label": f"file: {source.path_or_uri}", "path": source.path_or_uri},
        structured={
            "unit_kind": "source_artifact",
            "format": source.format,
            "byte_length": len(raw_bytes),
        },
        record_type=CoreRecordType.SOURCE_ARTIFACT.value,
    )
    units = _disambiguate_locators((artifact_unit, *bounded_units))
    records = tuple(
        _to_memory_record(
            source,
            unit,
            adapter_id=adapter.adapter_id,
            adapter_version=ADAPTER_VERSION,
            processed_at=timestamp,
            profile_version=profile_version,
        )
        for unit in units
    )
    return NormalizedDocument(
        source=source,
        raw_bytes=raw_bytes,
        records=records,
        adapter_id=adapter.adapter_id,
        adapter_version=ADAPTER_VERSION,
        profile_version=profile_version,
        processed_at=timestamp,
    )


def _normalize_optional_bytes(
    source: SourceRecord,
    raw_bytes: bytes,
    adapter: OptionalSourceAdapter,
    *,
    processed_at: datetime | None,
    profile_version: str,
    max_chunk_chars: int,
) -> NormalizedDocument:
    timestamp = ensure_utc(processed_at) if processed_at is not None else utc_now()
    try:
        provided = tuple(adapter.units(raw_bytes, source))
    except IngestionFailure:
        raise
    except Exception as error:
        raise IngestionFailure(
            source_id=source.source_id,
            adapter=adapter.adapter_id,
            stage="parse",
            category=ErrorCategory.INGESTION_FAILED,
            message="the optional adapter could not extract the registered source",
            recovery_action="inspect the sanitized adapter diagnostics and source declaration",
        ) from error
    if not provided or any(not isinstance(unit, OptionalAdapterUnit) for unit in provided):
        raise IngestionFailure(
            source_id=source.source_id,
            adapter=adapter.adapter_id,
            stage="parse",
            category=ErrorCategory.INGESTION_FAILED,
            message="the optional adapter returned no valid provider-neutral units",
            recovery_action="correct the optional adapter and repeat ingestion",
        )
    units = tuple(
        _Unit(
            title=unit.title,
            exact=unit.exact,
            locator=dict(unit.locator),
            structured=dict(unit.structured),
            record_type=unit.record_type,
            lifecycle_status=unit.lifecycle_status,
            valid_from=unit.valid_from,
            valid_to=unit.valid_to,
            profile_type=unit.profile_type,
            indexing=unit.indexing,
        )
        for unit in provided
    )
    bounded_units = tuple(
        part for unit in units for part in _bounded_unit(unit, max_chunk_chars=max_chunk_chars)
    )
    assert source.content_sha256 is not None
    artifact_unit = _Unit(
        title=source.path_or_uri,
        exact=(
            f"Optional-format source {source.path_or_uri}; exact bytes are available through "
            f"the source locator and SHA-256 {source.content_sha256}."
        ),
        locator={"label": f"file: {source.path_or_uri}", "path": source.path_or_uri},
        structured={
            "unit_kind": "source_artifact",
            "format": source.format,
            "byte_length": len(raw_bytes),
            "binary_or_optional": True,
        },
        record_type=CoreRecordType.SOURCE_ARTIFACT.value,
    )
    disambiguated = _disambiguate_locators((artifact_unit, *bounded_units))
    records = tuple(
        _to_memory_record(
            source,
            unit,
            adapter_id=adapter.adapter_id,
            adapter_version=adapter.adapter_version,
            processed_at=timestamp,
            profile_version=profile_version,
        )
        for unit in disambiguated
    )
    return NormalizedDocument(
        source=source,
        raw_bytes=raw_bytes,
        records=records,
        adapter_id=adapter.adapter_id,
        adapter_version=adapter.adapter_version,
        profile_version=profile_version,
        processed_at=timestamp,
    )


def normalize_many(
    project_root: Path,
    sources: Iterable[SourceRecord],
    *,
    processed_at: datetime | None = None,
    profile_version: str = DEFAULT_PROFILE_VERSION,
    max_file_bytes: int = 8 * 1024 * 1024,
    max_chunk_chars: int = 64 * 1024,
    optional_adapters: Iterable[OptionalSourceAdapter] = (),
) -> IngestionBatchResult:
    extensions = tuple(optional_adapters)
    documents: list[NormalizedDocument] = []
    failures: list[IngestionFailure] = []
    for source in sources:
        try:
            documents.append(
                normalize_source(
                    project_root,
                    source,
                    processed_at=processed_at,
                    profile_version=profile_version,
                    max_file_bytes=max_file_bytes,
                    max_chunk_chars=max_chunk_chars,
                    optional_adapters=extensions,
                )
            )
        except IngestionFailure as error:
            failures.append(error)
    return IngestionBatchResult(tuple(documents), tuple(failures))


def _bounded_unit(unit: _Unit, *, max_chunk_chars: int) -> tuple[_Unit, ...]:
    if len(unit.exact) <= max_chunk_chars:
        return (unit,)
    lines = unit.exact.splitlines(keepends=True)
    chunks: list[str] = []
    current = ""
    for line in lines:
        if current and len(current) + len(line) > max_chunk_chars:
            chunks.append(current)
            current = ""
        if len(line) > max_chunk_chars:
            if current:
                chunks.append(current)
                current = ""
            for offset in range(0, len(line), max_chunk_chars):
                chunks.append(line[offset : offset + max_chunk_chars])
        else:
            current += line
    if current:
        chunks.append(current)
    chunks = [chunk for chunk in chunks if chunk.strip()]
    result: list[_Unit] = []
    total = len(chunks)
    for index, exact in enumerate(chunks, start=1):
        locator = dict(unit.locator)
        base_label = str(locator.get("label", unit.title))
        locator["label"] = f"{base_label} [part {index}/{total}]"
        locator["part"] = index
        locator["parts"] = total
        structured = dict(unit.structured)
        structured["bounded_part"] = index
        structured["bounded_parts"] = total
        result.append(replace(unit, exact=exact, locator=locator, structured=structured))
    return tuple(result)


def _stable_locator(locator: Mapping[str, JsonValue]) -> str:
    stable = {
        key: value for key, value in locator.items() if key not in {"line_start", "line_end"}
    }
    return json.dumps(stable, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _disambiguate_locators(units: tuple[_Unit, ...]) -> tuple[_Unit, ...]:
    identities = [_stable_locator(unit.locator) for unit in units]
    totals = {identity: identities.count(identity) for identity in set(identities)}
    occurrences: dict[str, int] = {}
    result: list[_Unit] = []
    for unit, identity in zip(units, identities, strict=True):
        if totals[identity] == 1:
            result.append(unit)
            continue
        occurrence = occurrences.get(identity, 0) + 1
        occurrences[identity] = occurrence
        locator = dict(unit.locator)
        locator["occurrence"] = occurrence
        locator["occurrences"] = totals[identity]
        result.append(replace(unit, locator=locator))
    return tuple(result)


def _to_memory_record(
    source: SourceRecord,
    unit: _Unit,
    *,
    adapter_id: str,
    adapter_version: str,
    processed_at: datetime,
    profile_version: str,
) -> MemoryRecord:
    assert source.content_sha256 is not None
    label = str(unit.locator.get("label", unit.title))
    locator_identity = _stable_locator(unit.locator)
    identifier = stable_id("memory-record", source.source_id, locator_identity)
    record_id = f"mem_{identifier.replace('-', '')}"
    structured = dict(unit.structured)
    structured["_sys4ai"] = cast(
        JsonValue,
        {
            "extractor_version": adapter_version,
            "profile_version": profile_version,
            "extraction": "deterministic",
        },
    )
    path = None if source.origin_uri is not None else source.path_or_uri
    valid_from = ensure_utc(unit.valid_from) if unit.valid_from is not None else processed_at
    valid_to = ensure_utc(unit.valid_to) if unit.valid_to is not None else None
    return MemoryRecord(
        schema_version=SCHEMA_VERSION,
        api_version=API_VERSION,
        record_id=record_id,
        record_type=unit.record_type,
        profile_type=unit.profile_type,
        project_id=source.project_id,
        namespace=source.namespace,
        scope=source.scope,
        title=unit.title or label,
        content=MemoryContent(exact=unit.exact, summary=None, structured=structured),
        source=SourceAnchor(
            source_id=source.source_id,
            source_kind=source.source_kind,
            path=path,
            origin_uri=source.origin_uri,
            locator=dict(unit.locator),
            git_commit=source.git_commit,
            git_blob_sha=source.git_blob_sha,
            working_tree_state=source.working_tree_state,
            content_sha256=source.content_sha256,
        ),
        authority=AuthorityBinding(
            tier=source.authority_tier,
            trust_class=source.trust_class,
            canonical=source.canonicality == "canonical",
        ),
        epistemic=EpistemicMetadata(
            status=EpistemicStatus.SOURCE_STATEMENT,
            verification="deterministic-parse",
            confidence=1.0,
        ),
        lifecycle=LifecycleMetadata(
            status=unit.lifecycle_status,
            valid_from=valid_from,
            valid_to=valid_to,
            supersedes=(),
            superseded_by=(),
        ),
        security=SecurityMetadata(
            sensitivity=source.sensitivity,
            contains_secret=False,
            retention_policy=source.retention_policy,
        ),
        processing=ProcessingMetadata(
            parsed_by=f"sys4ai_memory.ingestion.{adapter_id}",
            adapter_version=adapter_version,
            profile_id=source.profile_id,
            deterministic_fields=(
                "title",
                "content.exact",
                "content.structured",
                "source.locator",
            ),
            model_extracted_fields=(),
            model_id=None,
            prompt_fingerprint=None,
            processed_at=processed_at,
        ),
        indexing=unit.indexing
        or IndexingMetadata(
            exact_fields=("record_id", "title", "content.exact", "content.structured"),
            lexical_fields=("title", "content.exact", "content.structured"),
            semantic_fields=(),
            graph_enabled=False,
        ),
        created_at=processed_at,
        updated_at=processed_at,
        version=1,
    )


def _mapping_identity(value: Mapping[object, object]) -> tuple[str | None, object | None]:
    for key in (
        "requirement_id",
        "event_id",
        "decision_id",
        "task_id",
        "component_id",
        "record_id",
        "source_id",
        "$id",
        "id",
        "title",
        "name",
    ):
        if key in value and isinstance(value[key], (str, int)):
            return key, value[key]
    return None, None


def _mapping_title(value: Mapping[object, object], fallback: str) -> str:
    _, identity = _mapping_identity(value)
    return str(identity) if identity is not None else fallback


def _record_type_for_mapping(value: Mapping[object, object]) -> str:
    if "requirement_id" in value:
        return CoreRecordType.REQUIREMENT.value
    if "event_id" in value or "occurred_at" in value:
        return CoreRecordType.EVENT.value
    if "decision_id" in value:
        return CoreRecordType.DECISION.value
    return CoreRecordType.SOURCE_FRAGMENT.value


def _record_type_for_identity(identity: str) -> str:
    if re.match(r"^(?:MEM-FR-|REQ[-_])", identity, re.IGNORECASE):
        return CoreRecordType.REQUIREMENT.value
    if re.match(r"^DEC[-_]", identity, re.IGNORECASE):
        return CoreRecordType.DECISION.value
    if re.match(r"^EVT[-_]", identity, re.IGNORECASE):
        return CoreRecordType.EVENT.value
    return CoreRecordType.SOURCE_FRAGMENT.value


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return ensure_utc(parsed)
    except ValueError:
        return None


def _lifecycle_for_mapping(
    value: Mapping[object, object],
) -> tuple[RecordStatus, datetime | None, datetime | None]:
    status_raw = value.get("status")
    try:
        status = RecordStatus(status_raw) if isinstance(status_raw, str) else RecordStatus.ACTIVE
    except ValueError:
        status = RecordStatus.ACTIVE
    valid_from = _parse_datetime(value.get("valid_from"))
    if valid_from is None:
        valid_from = _parse_datetime(value.get("occurred_at"))
    return status, valid_from, _parse_datetime(value.get("valid_to"))
