"""Provider-neutral health and drift aggregation."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Literal, Protocol

from pydantic import Field, model_validator

from sys4ai_memory.contracts._base import UtcDateTime
from sys4ai_memory.exact_index import IndexHealth
from sys4ai_memory.providers import ProviderHealth, ProviderHealthState
from sys4ai_memory.util import utc_now

from .models import HealthState, MetadataCode, ObservabilityModel, SourceIdentifier


class HealthComponentName(str):
    PROVIDER_CONNECTIVITY = "provider_connectivity"
    EXACT_INDEX = "exact_index"
    SOURCE_REGISTRY = "source_registry"
    SCHEMA_COMPATIBILITY = "schema_compatibility"
    STORAGE_ACCESS = "storage_access"
    DRIFT = "drift"


REQUIRED_COMPONENTS = frozenset(
    {
        HealthComponentName.PROVIDER_CONNECTIVITY,
        HealthComponentName.EXACT_INDEX,
        HealthComponentName.SOURCE_REGISTRY,
        HealthComponentName.SCHEMA_COMPATIBILITY,
        HealthComponentName.STORAGE_ACCESS,
        HealthComponentName.DRIFT,
    }
)


class HealthCount(ObservabilityModel):
    name: MetadataCode
    value: int = Field(ge=0)


class SourceIndexDriftReport(ObservabilityModel):
    """Content-free comparison of canonical source and derived-index identities."""

    registered_source_count: int = Field(ge=0)
    indexed_source_count: int = Field(ge=0)
    missing_index_source_count: int = Field(ge=0)
    unexpected_index_source_count: int = Field(ge=0)
    stale_source_count: int = Field(ge=0)
    configuration_fingerprint_matches: bool
    profile_fingerprint_matches: bool
    provider_fingerprint_matches: bool
    reason_codes: tuple[MetadataCode, ...]

    @property
    def drift_count(self) -> int:
        version_drift = sum(
            not value
            for value in (
                self.configuration_fingerprint_matches,
                self.profile_fingerprint_matches,
                self.provider_fingerprint_matches,
            )
        )
        return (
            self.missing_index_source_count
            + self.unexpected_index_source_count
            + self.stale_source_count
            + version_drift
        )

    @property
    def state(self) -> HealthState:
        return HealthState.HEALTHY if self.drift_count == 0 else HealthState.DEGRADED


class HealthComponent(ObservabilityModel):
    name: MetadataCode
    state: HealthState
    detail_code: MetadataCode
    checked_at: UtcDateTime
    fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    counts: tuple[HealthCount, ...] = ()

    @model_validator(mode="after")
    def validate_component(self) -> HealthComponent:
        names = tuple(item.name for item in self.counts)
        if len(names) != len(set(names)):
            raise ValueError("health count names must be unique")
        return self


class CompositeHealth(ObservabilityModel):
    record_kind: Literal["composite_health"] = "composite_health"
    project_id: MetadataCode
    checked_at: UtcDateTime
    liveness: HealthState
    readiness: HealthState
    drift: HealthState
    components: tuple[HealthComponent, ...]

    @model_validator(mode="after")
    def validate_report(self) -> CompositeHealth:
        names = tuple(item.name for item in self.components)
        if len(names) != len(set(names)):
            raise ValueError("health component names must be unique")
        if set(names) != REQUIRED_COMPONENTS:
            missing = sorted(REQUIRED_COMPONENTS - set(names))
            extra = sorted(set(names) - REQUIRED_COMPONENTS)
            raise ValueError(f"health components are incomplete: missing={missing}, extra={extra}")
        return self


class HealthProbe(Protocol):
    """Injectable adapter boundary for one component probe."""

    def __call__(self) -> HealthComponent: ...


def _worst(states: Iterable[HealthState]) -> HealthState:
    ranks = {
        HealthState.HEALTHY: 0,
        HealthState.DEGRADED: 1,
        HealthState.UNAVAILABLE: 2,
    }
    return max(states, key=ranks.__getitem__)


class HealthAggregator:
    """Aggregate six injected metadata probes without opening storage or providers."""

    def __init__(self, probes: Iterable[HealthProbe]) -> None:
        self._probes = tuple(probes)

    def check(self, *, project_id: str, checked_at: datetime | None = None) -> CompositeHealth:
        components = tuple(probe() for probe in self._probes)
        by_name = {component.name: component for component in components}
        if len(by_name) != len(components) or set(by_name) != REQUIRED_COMPONENTS:
            missing = sorted(REQUIRED_COMPONENTS - set(by_name))
            raise ValueError(f"health probes must provide each required component once: {missing}")
        drift = by_name[HealthComponentName.DRIFT].state
        readiness = _worst(component.state for component in components)
        # Reaching this aggregation point proves the service process is responsive.
        # Dependency state belongs in readiness and the component list.
        return CompositeHealth(
            project_id=project_id,
            checked_at=checked_at or utc_now(),
            liveness=HealthState.HEALTHY,
            readiness=readiness,
            drift=drift,
            components=tuple(sorted(components, key=lambda item: item.name)),
        )


def provider_health_component(result: ProviderHealth) -> HealthComponent:
    state = {
        ProviderHealthState.ALIVE: HealthState.HEALTHY,
        ProviderHealthState.READY: HealthState.HEALTHY,
        ProviderHealthState.DEGRADED: HealthState.DEGRADED,
        ProviderHealthState.UNAVAILABLE: HealthState.UNAVAILABLE,
    }[result.state]
    return HealthComponent(
        name=HealthComponentName.PROVIDER_CONNECTIVITY,
        state=state,
        detail_code=f"provider_{result.state.value}",
        checked_at=result.checked_at,
        counts=(HealthCount(name="component_count", value=len(result.components)),),
    )


def exact_index_health_component(
    result: IndexHealth,
    *,
    checked_at: datetime,
) -> HealthComponent:
    if not result.fts5_available:
        state = HealthState.UNAVAILABLE
        detail = "fts5_unavailable"
    elif result.active_generation_id is None:
        state = HealthState.DEGRADED
        detail = "generation_missing"
    else:
        state = HealthState.HEALTHY
        detail = "index_ready"
    return HealthComponent(
        name=HealthComponentName.EXACT_INDEX,
        state=state,
        detail_code=detail,
        checked_at=checked_at,
        counts=(
            HealthCount(name="source_count", value=result.current_source_count),
            HealthCount(name="record_count", value=result.current_record_count),
        ),
    )


def detect_source_index_drift(
    *,
    registered_source_ids: Iterable[SourceIdentifier],
    indexed_source_ids: Iterable[SourceIdentifier],
    stale_source_ids: Iterable[SourceIdentifier] = (),
    expected_configuration_fingerprint: str,
    active_configuration_fingerprint: str,
    expected_profile_fingerprint: str,
    active_profile_fingerprint: str,
    expected_provider_fingerprint: str,
    active_provider_fingerprint: str,
) -> SourceIndexDriftReport:
    fingerprints = (
        expected_configuration_fingerprint,
        active_configuration_fingerprint,
        expected_profile_fingerprint,
        active_profile_fingerprint,
        expected_provider_fingerprint,
        active_provider_fingerprint,
    )
    if any(
        len(value) != 64 or any(character not in "0123456789abcdef" for character in value)
        for value in fingerprints
    ):
        raise ValueError("drift comparison requires lowercase SHA-256 fingerprints")
    registered = frozenset(registered_source_ids)
    indexed = frozenset(indexed_source_ids)
    stale = frozenset(stale_source_ids)
    if not stale.issubset(registered | indexed):
        raise ValueError("stale source identities must belong to the compared source sets")
    configuration_matches = expected_configuration_fingerprint == active_configuration_fingerprint
    profile_matches = expected_profile_fingerprint == active_profile_fingerprint
    provider_matches = expected_provider_fingerprint == active_provider_fingerprint
    reason_codes: list[str] = []
    if registered - indexed:
        reason_codes.append("missing_index_sources")
    if indexed - registered:
        reason_codes.append("unexpected_index_sources")
    if stale:
        reason_codes.append("stale_source_revisions")
    if not configuration_matches:
        reason_codes.append("configuration_fingerprint_mismatch")
    if not profile_matches:
        reason_codes.append("profile_fingerprint_mismatch")
    if not provider_matches:
        reason_codes.append("provider_fingerprint_mismatch")
    return SourceIndexDriftReport(
        registered_source_count=len(registered),
        indexed_source_count=len(indexed),
        missing_index_source_count=len(registered - indexed),
        unexpected_index_source_count=len(indexed - registered),
        stale_source_count=len(stale),
        configuration_fingerprint_matches=configuration_matches,
        profile_fingerprint_matches=profile_matches,
        provider_fingerprint_matches=provider_matches,
        reason_codes=tuple(reason_codes),
    )


def drift_health_component(
    report: SourceIndexDriftReport,
    *,
    checked_at: datetime,
) -> HealthComponent:
    return HealthComponent(
        name=HealthComponentName.DRIFT,
        state=report.state,
        detail_code="drift_clear" if report.drift_count == 0 else "source_index_drift",
        checked_at=checked_at,
        counts=(
            HealthCount(name="drift_count", value=report.drift_count),
            HealthCount(name="missing_index_source_count", value=report.missing_index_source_count),
            HealthCount(
                name="unexpected_index_source_count",
                value=report.unexpected_index_source_count,
            ),
            HealthCount(name="stale_source_count", value=report.stale_source_count),
        ),
    )


def metadata_health_probe(
    *,
    name: str,
    probe: Callable[[], tuple[HealthState, str, tuple[HealthCount, ...], str | None]],
    clock: Callable[[], datetime] = utc_now,
) -> HealthProbe:
    """Adapt a side-effect-free metadata probe to the aggregate contract."""

    if name not in REQUIRED_COMPONENTS:
        raise ValueError(f"unknown health component: {name}")

    def check() -> HealthComponent:
        state, detail, counts, fingerprint = probe()
        return HealthComponent(
            name=name,
            state=state,
            detail_code=detail,
            checked_at=clock(),
            fingerprint=fingerprint,
            counts=counts,
        )

    return check
