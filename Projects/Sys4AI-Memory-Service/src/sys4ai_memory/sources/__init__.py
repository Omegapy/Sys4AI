"""Registry-driven source discovery."""

from .discovery import (
    DiscoveryDecision,
    DiscoveryDisposition,
    DiscoveryReason,
    DiscoveryReport,
    SourceDiscovery,
    discover_sources,
)
from .registry import (
    FIXTURE_SOURCE_HEADER,
    PROFILE_HEADER,
    RELATION_HEADER,
    SOURCE_HEADER,
    ProfileRegistryEntry,
    RegistryBundle,
    RegistryValidationError,
    RelationRegistryEntry,
    SourceRegistryEntry,
    load_profile_registry,
    load_registry_bundle,
    load_relation_registry,
    load_source_registry,
    source_entries_by_project,
)

__all__ = [
    "FIXTURE_SOURCE_HEADER",
    "PROFILE_HEADER",
    "RELATION_HEADER",
    "SOURCE_HEADER",
    "DiscoveryDecision",
    "DiscoveryDisposition",
    "DiscoveryReason",
    "DiscoveryReport",
    "ProfileRegistryEntry",
    "RegistryBundle",
    "RegistryValidationError",
    "RelationRegistryEntry",
    "SourceDiscovery",
    "SourceRegistryEntry",
    "discover_sources",
    "load_profile_registry",
    "load_registry_bundle",
    "load_relation_registry",
    "load_source_registry",
    "source_entries_by_project",
]
