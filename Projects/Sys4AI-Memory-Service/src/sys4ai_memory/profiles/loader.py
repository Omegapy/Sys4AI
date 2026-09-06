"""Fail-closed, deterministic loading for memory profiles."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version
from pydantic import ValidationError

from sys4ai_memory.contracts import API_VERSION, AuthorityTier, MemoryProfile
from sys4ai_memory.sources.registry import ProfileRegistryEntry
from sys4ai_memory.util import canonical_json_bytes, resolve_within, sha256_bytes

from .models import ProfileDefinition, ProfileSourceAuthority

MAX_PROFILE_BYTES = 1_048_576
_UNTRUSTED_SOURCE = ProfileSourceAuthority(
    source_ref="implicit-untrusted-profile-source",
    authority_tier=AuthorityTier.UNTRUSTED_CONTENT,
)


class ProfileError(ValueError):
    """A profile or profile set is unsafe, invalid, or incompatible."""


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects ambiguous duplicate mapping keys."""


def _construct_mapping(
    loader: _UniqueKeySafeLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    loader.flatten_mapping(node)
    result: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as error:
            raise ProfileError("YAML mapping keys must be scalar") from error
        if duplicate:
            raise ProfileError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


@dataclass(frozen=True, slots=True)
class LoadedProfile:
    profile: ProfileDefinition
    source_path: Path
    content_sha256: str
    source_authority: ProfileSourceAuthority


@dataclass(frozen=True, slots=True)
class ProfileSet:
    profiles: tuple[LoadedProfile, ...]
    fingerprint: str
    record_type_owners: dict[str, str]
    relation_owners: dict[str, str]
    adapter_owners: dict[str, str]
    source_authorities: dict[str, ProfileSourceAuthority]

    @property
    def profile_ids(self) -> tuple[str, ...]:
        return tuple(item.profile.profile_id for item in self.profiles)


@dataclass(frozen=True, slots=True)
class RepresentationChange:
    changed: bool
    requires_rebuild: bool
    reasons: tuple[str, ...]


def _read_payload(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ProfileError(f"cannot read profile: {path}") from error
    if len(raw) > MAX_PROFILE_BYTES:
        raise ProfileError(f"profile exceeds {MAX_PROFILE_BYTES} bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ProfileError("profile must be UTF-8") from error
    try:
        if path.suffix.casefold() == ".json":
            payload = json.loads(text)
        elif path.suffix.casefold() in {".yaml", ".yml"}:
            payload = yaml.load(text, Loader=_UniqueKeySafeLoader)  # noqa: S506
        else:
            raise ProfileError("profile extension must be .json, .yaml, or .yml")
    except (json.JSONDecodeError, yaml.YAMLError) as error:
        raise ProfileError(f"profile syntax is invalid: {error}") from error
    if not isinstance(payload, dict):
        raise ProfileError("profile root must be an object")
    return payload


def _load_profile_definition(
    path: Path,
    *,
    trusted_project_root: Path,
    source_authority: ProfileSourceAuthority,
    validate_authority: bool = True,
) -> LoadedProfile:
    """Parse one profile after its source authority has been resolved externally."""

    if not trusted_project_root.is_absolute() or trusted_project_root.is_symlink():
        raise ProfileError("trusted project root must be an absolute non-symlink directory")
    root = trusted_project_root.resolve(strict=True)
    if path.is_symlink() or not path.is_file():
        raise ProfileError("profile must be a regular non-symlink file")
    resolved = path.resolve(strict=True)
    try:
        relative_path = resolved.relative_to(root)
    except ValueError as error:
        raise ProfileError("profile path escapes the trusted project root") from error
    try:
        resolve_within(root, relative_path)
    except ValueError as error:
        raise ProfileError("profile path crosses an unsafe symlink") from error
    payload = _read_payload(resolved)
    try:
        profile = ProfileDefinition.model_validate(payload)
    except ValidationError as error:
        raise ProfileError(f"profile schema is invalid: {error}") from error
    if validate_authority:
        _validate_instruction_authority(profile, source_authority)
    return LoadedProfile(
        profile=profile,
        source_path=resolved,
        content_sha256=sha256_bytes(resolved.read_bytes()),
        source_authority=source_authority,
    )


def load_profile(
    path: Path,
    *,
    trusted_project_root: Path,
    source_authority: ProfileSourceAuthority | None = None,
) -> LoadedProfile:
    """Load one confined profile under an externally granted authority ceiling."""

    return _load_profile_definition(
        path,
        trusted_project_root=trusted_project_root,
        source_authority=source_authority or _UNTRUSTED_SOURCE,
    )


def _validate_instruction_authority(
    profile: ProfileDefinition,
    source_authority: ProfileSourceAuthority,
) -> None:
    source_rank = int(source_authority.authority_tier.value[1:])
    for kind, reference in profile.behavior_references():
        requested_rank = int(reference.authority_tier.value[1:])
        if requested_rank < source_rank:
            raise ProfileError(
                f"profile {profile.profile_id} {kind} {reference.ref!r} requests "
                f"{reference.authority_tier.value}, exceeding source authority "
                f"{source_authority.authority_tier.value} from {source_authority.source_ref}"
            )


def _validate_api(profile: MemoryProfile, api_version: str) -> None:
    try:
        compatible = Version(api_version) in SpecifierSet(profile.compatibility.sys4ai_memory_api)
    except (InvalidSpecifier, InvalidVersion) as error:
        raise ProfileError(
            f"profile {profile.profile_id} has invalid API compatibility metadata"
        ) from error
    if not compatible:
        raise ProfileError(
            f"profile {profile.profile_id} is incompatible with memory API {api_version}"
        )


def _ordered_profiles(
    loaded: dict[str, LoadedProfile],
    *,
    required_base: str,
) -> tuple[LoadedProfile, ...]:
    if required_base not in loaded:
        raise ProfileError(f"required base profile is missing: {required_base}")
    if loaded[required_base].profile.extends:
        raise ProfileError("base profile cannot extend another profile")
    visiting: set[str] = set()
    visited: set[str] = set()
    order: list[LoadedProfile] = []

    def visit(profile_id: str) -> None:
        if profile_id in visited:
            return
        if profile_id in visiting:
            raise ProfileError(f"profile inheritance cycle includes {profile_id}")
        item = loaded.get(profile_id)
        if item is None:
            raise ProfileError(f"profile dependency is missing: {profile_id}")
        visiting.add(profile_id)
        if len(item.profile.extends) != len(set(item.profile.extends)):
            raise ProfileError(f"profile {profile_id} has duplicate parent profiles")
        for parent in sorted(item.profile.extends):
            visit(parent)
        visiting.remove(profile_id)
        visited.add(profile_id)
        order.append(item)

    visit(required_base)
    for profile_id in sorted(loaded):
        visit(profile_id)
    for profile_id, item in loaded.items():
        if profile_id == required_base:
            continue
        reachable: set[str] = set()
        frontier = list(item.profile.extends)
        while frontier:
            parent_id = frontier.pop()
            if parent_id in reachable:
                continue
            reachable.add(parent_id)
            frontier.extend(loaded[parent_id].profile.extends)
        if required_base not in reachable:
            raise ProfileError(f"profile {profile_id} does not extend {required_base}")
    if order[0].profile.profile_id != required_base:
        raise ProfileError("base profile must load first")
    return tuple(order)


def _register_unique(
    owners: dict[str, str],
    names: tuple[str, ...],
    *,
    profile_id: str,
    kind: str,
) -> None:
    for name in names:
        if prior := owners.get(name):
            raise ProfileError(f"profile {profile_id} conflicts with {prior} on {kind} {name!r}")
        owners[name] = profile_id


def _validate_local_references(item: LoadedProfile, root: Path) -> None:
    profile = item.profile
    references = [record.schema_ref for record in profile.record_types]
    references.extend(reference.ref for _kind, reference in profile.behavior_references())
    references.extend(reference.ref for reference in profile.evaluations)
    for reference in references:
        if "://" in reference or not any(marker in reference for marker in ("/", ".")):
            continue
        try:
            resolved = resolve_within(root, reference)
        except (FileNotFoundError, ValueError) as error:
            raise ProfileError(
                f"profile {profile.profile_id} has an unsafe or missing reference: {reference}"
            ) from error
        if resolved.is_symlink() or not resolved.is_file():
            raise ProfileError(
                f"profile {profile.profile_id} reference must be a regular file: {reference}"
            )


def load_profile_set(
    paths: tuple[Path, ...],
    *,
    trusted_project_root: Path,
    enabled_capabilities: frozenset[str],
    source_authorities: Mapping[str, ProfileSourceAuthority] | None = None,
    required_base: str = "base@1",
    api_version: str = API_VERSION,
) -> ProfileSet:
    """Load, order, and compose profiles without silently resolving conflicts."""

    if not paths:
        raise ProfileError("at least one profile is required")
    preliminary = tuple(
        _load_profile_definition(
            path,
            trusted_project_root=trusted_project_root,
            source_authority=_UNTRUSTED_SOURCE,
            validate_authority=False,
        )
        for path in paths
    )
    profile_ids = tuple(item.profile.profile_id for item in preliminary)
    if source_authorities:
        unknown = sorted(set(source_authorities) - set(profile_ids))
        if unknown:
            raise ProfileError(
                f"source authority supplied for unknown profile IDs: {', '.join(unknown)}"
            )
    authorities = source_authorities or {}
    items_list: list[LoadedProfile] = []
    for item in preliminary:
        profile_id = item.profile.profile_id
        authority = authorities.get(profile_id, _UNTRUSTED_SOURCE)
        _validate_instruction_authority(item.profile, authority)
        items_list.append(replace(item, source_authority=authority))
    items = tuple(items_list)
    loaded: dict[str, LoadedProfile] = {}
    for item in items:
        profile_id = item.profile.profile_id
        if profile_id in loaded:
            raise ProfileError(f"duplicate profile ID: {profile_id}")
        loaded[profile_id] = item
    ordered = _ordered_profiles(loaded, required_base=required_base)

    record_type_owners: dict[str, str] = {}
    relation_owners: dict[str, str] = {}
    adapter_owners: dict[str, str] = {}
    for item in ordered:
        profile = item.profile
        _validate_api(profile, api_version)
        missing = sorted(set(profile.compatibility.required_capabilities) - enabled_capabilities)
        if missing:
            raise ProfileError(
                f"profile {profile.profile_id} requires disabled capabilities: {', '.join(missing)}"
            )
        _validate_local_references(item, trusted_project_root.resolve(strict=True))
        _register_unique(
            record_type_owners,
            tuple(record.name for record in profile.record_types),
            profile_id=profile.profile_id,
            kind="record type",
        )
        _register_unique(
            relation_owners,
            profile.relations,
            profile_id=profile.profile_id,
            kind="relation",
        )
        _register_unique(
            adapter_owners,
            tuple(adapter.id for adapter in profile.source_adapters),
            profile_id=profile.profile_id,
            kind="adapter",
        )

    fingerprint_payload = [
        {
            "profile": item.profile.model_dump(mode="json"),
            "content_sha256": item.content_sha256,
            "source_authority": item.source_authority.model_dump(mode="json"),
        }
        for item in ordered
    ]
    return ProfileSet(
        profiles=ordered,
        fingerprint=sha256_bytes(canonical_json_bytes(fingerprint_payload)),
        record_type_owners=record_type_owners,
        relation_owners=relation_owners,
        adapter_owners=adapter_owners,
        source_authorities={item.profile.profile_id: item.source_authority for item in ordered},
    )


def _representation_payload(profile: MemoryProfile) -> dict[str, object]:
    payload: dict[str, object] = {
        "record_types": [item.model_dump(mode="json") for item in profile.record_types],
        "relations": list(profile.relations),
        "source_adapters": [item.model_dump(mode="json") for item in profile.source_adapters],
        "write_policies": [item.model_dump(mode="json") for item in profile.write_policies],
        "retrieval_strategies": [
            item.model_dump(mode="json") for item in profile.retrieval_strategies
        ],
    }
    if isinstance(profile, ProfileDefinition):
        payload.update(
            {
                "retention_policies": [
                    item.model_dump(mode="json") for item in profile.retention_policies
                ],
                "context_assembly_rules": [
                    item.model_dump(mode="json") for item in profile.context_assembly_rules
                ],
                "reranking_rules": [
                    item.model_dump(mode="json") for item in profile.reranking_rules
                ],
                "instructions": [item.model_dump(mode="json") for item in profile.instructions],
            }
        )
    return payload


def assess_representation_change(
    previous: MemoryProfile,
    current: MemoryProfile,
) -> RepresentationChange:
    """Report whether a profile change requires migration or a rebuild."""

    reasons: list[str] = []
    if previous.profile_id != current.profile_id:
        reasons.append("profile identity changed")
    if _representation_payload(previous) != _representation_payload(current):
        reasons.append("stored representation inputs changed")
    if previous.compatibility != current.compatibility:
        reasons.append("compatibility requirements changed")
    changed = bool(reasons)
    return RepresentationChange(
        changed=changed,
        requires_rebuild=changed,
        reasons=tuple(reasons),
    )


def validate_profile_registrations(
    profile_set: ProfileSet,
    registrations: tuple[ProfileRegistryEntry, ...],
) -> None:
    """Verify loaded definitions against the canonical profile registry projection."""

    by_id = {item.profile_id: item for item in registrations}
    if len(by_id) != len(registrations):
        raise ProfileError("profile registry contains duplicate profile IDs")
    loaded_ids = set(profile_set.profile_ids)
    missing_definitions = sorted(set(by_id) - loaded_ids)
    unregistered = sorted(loaded_ids - set(by_id))
    if missing_definitions:
        raise ProfileError(
            f"registered profile definitions were not loaded: {', '.join(missing_definitions)}"
        )
    if unregistered:
        raise ProfileError(f"loaded profiles are not registered: {', '.join(unregistered)}")

    for loaded in profile_set.profiles:
        profile = loaded.profile
        registration = by_id[profile.profile_id]
        expected_parent = registration.extends_profile_id
        registered_parents = () if expected_parent is None else (expected_parent,)
        checks: tuple[tuple[str, object, object], ...] = (
            ("version", profile.version, registration.profile_version),
            ("parent profiles", profile.extends, registered_parents),
            (
                "record types",
                tuple(item.name for item in profile.record_types),
                registration.record_types,
            ),
            ("relations", profile.relations, registration.relation_types),
            (
                "source adapters",
                tuple(item.id for item in profile.source_adapters),
                registration.source_adapters,
            ),
            (
                "API compatibility",
                profile.compatibility.sys4ai_memory_api,
                registration.api_compatibility,
            ),
        )
        for label, actual, registered in checks:
            if actual != registered:
                raise ProfileError(
                    f"profile {profile.profile_id} {label} do not match the registry"
                )
