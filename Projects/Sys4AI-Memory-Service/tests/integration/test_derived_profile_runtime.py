from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.contracts import (
    PUBLIC_OPERATION_CATALOG,
    AuthorityTier,
    ErrorCategory,
    MemoryScope,
    RetrievalMode,
    RetrievalResult,
    ScopeReference,
    Sensitivity,
    SourceRecord,
    TrustClass,
)
from sys4ai_memory.exact_index import ExactIndex
from sys4ai_memory.ingestion import (
    IngestionSynchronizer,
    OptionalAdapterUnit,
    SoftwareEngineeringPythonAdapter,
)
from sys4ai_memory.interfaces import DispatchSuccess, InterfaceIdentity, MemoryClient
from sys4ai_memory.profiles import (
    ProfileSet,
    ProfileSourceAuthority,
    load_profile_set,
    validate_profile_registrations,
)
from sys4ai_memory.providers import (
    InMemoryProviderConfig,
    ProviderContext,
    ProviderInitializationRequest,
    ProviderMutation,
)
from sys4ai_memory.providers.in_memory import InMemoryProvider
from sys4ai_memory.retrieval import RetrievalEngine
from sys4ai_memory.security import ProjectBoundary
from sys4ai_memory.service import ServiceComponents
from sys4ai_memory.sources import (
    ProfileRegistryEntry,
    RegistryBundle,
    SourceDiscovery,
    SourceRegistryEntry,
    load_profile_registry,
    load_relation_registry,
    load_source_registry,
)
from tests.providers.helpers import policy
from tests.service.test_dispatcher import DATASET_ID, PROJECT_ID, _identity, _service

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]
PRODUCT_ROOT = Path(__file__).parents[2]


def _profile_payload(
    profile_id: str,
    *,
    version: str,
    extends: tuple[str, ...],
    record_types: tuple[str, ...],
    adapters: tuple[tuple[str, str], ...],
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "api_version": "1.0",
        "profile_id": profile_id,
        "version": version,
        "extends": list(extends),
        "compatibility": {
            "sys4ai_memory_api": ">=1.0,<2.0",
            "required_capabilities": ["exact", "semantic"],
        },
        "record_types": [
            {
                "name": record_type,
                "schema_ref": "schemas/record.json",
                "exact_fields": ["record_id", "title"],
                "semantic_fields": ["title", "content.exact"],
                "lexical_fields": ["title", "content.exact"],
            }
            for record_type in record_types
        ],
        "relations": [],
        "source_adapters": [
            {"id": adapter_id, "formats": [format_name]}
            for adapter_id, format_name in adapters
        ],
        "write_policies": [{"ref": f"{profile_id}-write-policy"}],
        "retrieval_strategies": [{"ref": f"{profile_id}-retrieval"}],
        "evaluations": [{"ref": f"{profile_id}-evaluation"}],
    }


def _profile_set(root: Path) -> ProfileSet:
    schema = root / "schemas/record.json"
    schema.parent.mkdir()
    schema.write_text("{}\n", encoding="utf-8")
    base = root / "profiles/base.json"
    extension = root / "profiles/fixture-derived.json"
    base.parent.mkdir()
    base.write_text(
        json.dumps(
            _profile_payload(
                "base@1",
                version="1.0.0",
                extends=(),
                record_types=("SourceArtifact",),
                adapters=(("text", "text"),),
            )
        ),
        encoding="utf-8",
    )
    extension.write_text(
        json.dumps(
            _profile_payload(
                "fixture-derived@1",
                version="1.2.0",
                extends=("base@1",),
                record_types=("DomainFact",),
                adapters=(("fixture-domain@1", "domain"),),
            )
        ),
        encoding="utf-8",
    )
    return load_profile_set(
        (extension, base),
        trusted_project_root=root,
        enabled_capabilities=frozenset({"exact", "semantic"}),
        source_authorities={
            "base@1": ProfileSourceAuthority(
                source_ref="fixture-base-profile",
                authority_tier=AuthorityTier.PROJECT_CONTROL,
            ),
            "fixture-derived@1": ProfileSourceAuthority(
                source_ref="fixture-derived-profile",
                authority_tier=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
            ),
        },
    )


def _profile_registrations(profile_set: ProfileSet) -> tuple[ProfileRegistryEntry, ...]:
    rows: list[ProfileRegistryEntry] = []
    for loaded in profile_set.profiles:
        profile = loaded.profile
        rows.append(
            ProfileRegistryEntry(
                profile_id=profile.profile_id,
                profile_name=profile.profile_id,
                profile_version=profile.version,
                lifecycle_status="active",
                implementation_status="verified",
                extends_profile_id=profile.extends[0] if profile.extends else None,
                schema_ref="schemas/record.json",
                config_ref=loaded.source_path.relative_to(
                    loaded.source_path.parents[1]
                ).as_posix(),
                record_types=tuple(item.name for item in profile.record_types),
                relation_types=profile.relations,
                source_adapters=tuple(item.id for item in profile.source_adapters),
                write_policy_ref=profile.write_policies[0].ref,
                migration_ref=None,
                api_compatibility=profile.compatibility.sys4ai_memory_api,
                owner="fixture",
                authority_basis=("temporary integration fixture",),
                notes=None,
            )
        )
    return tuple(rows)


def _source_entry() -> SourceRegistryEntry:
    return SourceRegistryEntry(
        source_id="src_fixture-derived-domain",
        project_id=PROJECT_ID,
        path_or_uri="domain/widget.domain",
        path_pattern=None,
        source_kind="file",
        format="domain",
        canonicality="canonical",
        content_role="project-knowledge",
        authority_tier=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
        trust_class=TrustClass.PROJECT_AUTHORED,
        sensitivity=Sensitivity.INTERNAL,
        namespace=f"project/{PROJECT_ID}/fixture-domain",
        profile_id="fixture-derived@1",
        ingestion_adapter="fixture-domain@1",
        chunking_profile="fixture-domain@1",
        schema_ref=None,
        refresh_mode="manual",
        retention_policy="canonical",
        owner="fixture",
        write_policy="review-required",
        include_flag=True,
        notes="Temporary derived-agent integration source",
    )


class _DomainAdapter:
    adapter_id = "fixture-domain@1"
    adapter_version = "1.0.0"
    formats = frozenset({"domain"})

    def units(
        self,
        raw_bytes: bytes,
        source: SourceRecord,
    ) -> tuple[OptionalAdapterUnit, ...]:
        text = raw_bytes.decode("utf-8")
        return (
            OptionalAdapterUnit(
                title="Calibration widget",
                exact=text,
                locator={"label": "domain-object: calibration-widget"},
                structured={"unit_kind": "domain_fact", "source_id": source.source_id},
                record_type="DomainFact",
                profile_type="fixture-derived@1:DomainFact",
            ),
        )


class _UndeclaredRecordAdapter(_DomainAdapter):
    def units(
        self,
        raw_bytes: bytes,
        source: SourceRecord,
    ) -> tuple[OptionalAdapterUnit, ...]:
        unit = super().units(raw_bytes, source)[0]
        return (
            OptionalAdapterUnit(
                title=unit.title,
                exact=unit.exact,
                locator=unit.locator,
                structured=unit.structured,
                record_type="UndeclaredFact",
                profile_type="fixture-derived@1:UndeclaredFact",
            ),
        )


def _discovery(root: Path, entry: SourceRegistryEntry):
    return SourceDiscovery(
        project_root=root,
        project_id=PROJECT_ID,
        entries=(entry,),
    ).discover()


def _initialize_provider(provider: InMemoryProvider) -> None:
    context = ProviderContext(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        principal_id=_identity().principal_id,
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=PROJECT_ID),
        trace_id="trace_derived_profile_provider_setup",
    )
    asyncio.run(
        provider.initialize(
            ProviderInitializationRequest(
                context=context,
                configuration_fingerprint="c" * 64,
                dry_run=False,
                path_boundaries_validated=True,
                exclusions_validated=True,
                discovery_dry_run_approved=True,
                authorization=policy(ProviderMutation.INITIALIZE, context),
            )
        )
    )


def _install_agent_permissions(permission_path: Path) -> None:
    document = json.loads(permission_path.read_text(encoding="utf-8"))
    document["revision"] = "permissions-derived-profile-runtime-1"
    template = document["grants"][0]
    document["grants"].extend(
        {
            **template,
            "grant_id": f"derived-profile-{principal_id}",
            "principal_id": principal_id,
            "permissions": ["read"],
            "operations": ["memory.recall"],
        }
        for principal_id in ("agent-alpha", "agent-beta")
    )
    permission_path.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")


def _agent_client(service, principal_id: str) -> MemoryClient:
    return MemoryClient(
        service,
        identity=InterfaceIdentity(
            principal_id=principal_id,
            agent_type=f"{principal_id}-derived",
            run_id=f"run-{principal_id}",
        ),
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    )


def test_temporary_extension_syncs_and_serves_two_agents_without_api_change(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    (root / "domain").mkdir()
    (root / "domain/widget.domain").write_text(
        "Calibration widget torque procedure.\n",
        encoding="utf-8",
    )
    profiles = _profile_set(root)
    registrations = _profile_registrations(profiles)
    validate_profile_registrations(profiles, registrations)
    bundle = RegistryBundle(
        sources=(_source_entry(),),
        profiles=registrations,
        relations=(),
    )
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
    )
    _initialize_provider(provider)
    components = ServiceComponents()
    service, audit, permission_path = _service(root, components=components)
    _install_agent_permissions(permission_path)
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    authorization = AuthorizationService(
        CanonicalPermissionEnvelopeLoader(
            boundary,
            "control_records/memory/permissions.json",
        )
    )
    operation_catalog_before = tuple(PUBLIC_OPERATION_CATALOG)

    with ExactIndex(":memory:") as index:
        components.registry_loader = lambda: bundle
        components.synchronizer = IngestionSynchronizer(
            project_root=root,
            index_writer=index,
            profile_set=profiles,
            optional_adapters=(_DomainAdapter(),),
        )
        components.provider = provider
        components.retrieval = RetrievalEngine(
            project_id=PROJECT_ID,
            dataset_id=DATASET_ID,
            authorizer=authorization,
            exact_backend=index,
            exact_record_resolver=index,
            provider=provider,
        )
        synchronized = MemoryClient(
            service,
            identity=_identity(),
            project_id=PROJECT_ID,
            dataset_id=DATASET_ID,
        ).sync(
            idempotency_key="derived-profile-sync",
            request_id="mrq_derived_profile_sync",
            trace_id="trace_derived_profile_sync",
        )
        assert isinstance(synchronized, DispatchSuccess)
        assert synchronized.result["failure_count"] == 0

        results: list[RetrievalResult] = []
        for principal_id in ("agent-alpha", "agent-beta"):
            response = _agent_client(service, principal_id).recall(
                "calibration widget",
                mode=RetrievalMode.SEMANTIC,
                request_id=f"mrq_derived_profile_recall_{principal_id}",
                trace_id=f"trace_derived_profile_recall_{principal_id}",
            )
            assert isinstance(response, DispatchSuccess)
            results.append(RetrievalResult.model_validate(response.result["retrieval"]))

        evidence = [
            result.results[0].model_dump(exclude={"scores", "selection_reason"})
            for result in results
        ]
        assert evidence[0] == evidence[1]
        assert results[0].results[0].record_type == "DomainFact"
        records = index.current_source_records(
            project_id=PROJECT_ID,
            source_id="src_fixture-derived-domain",
        )
        assert {record.processing.profile_id for record in records} == {
            "fixture-derived@1"
        }
        assert {
            record.content.structured["_sys4ai"]["profile_version"]  # type: ignore[index]
            for record in records
        } == {"1.2.0"}

    assert tuple(PUBLIC_OPERATION_CATALOG) == operation_catalog_before
    assert [event.outcome for event in audit.events()].count("failed") == 0
    assert not (root / "profiles/software-engineering").exists()


def test_approved_software_engineering_profile_serves_two_agents_without_api_change(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    (root / "src").mkdir()
    (root / "src/example.py").write_text(
        '''BUILD_TARGET = "wheel"

class ParserError(Exception):
    pass

def parse_payload(value: str) -> str:
    return value.strip()

def test_parse_payload() -> None:
    assert parse_payload(" ok ") == "ok"
''',
        encoding="utf-8",
    )
    profiles = load_profile_set(
        (
            PRODUCT_ROOT / "profiles/base/profile.yaml",
            PRODUCT_ROOT / "profiles/software-engineering/profile.yaml",
        ),
        trusted_project_root=PRODUCT_ROOT,
        enabled_capabilities=frozenset(
            {
                "service_health",
                "source_registry",
                "ingestion",
                "exact",
                "lexical",
                "semantic",
                "graph",
                "provenance_explanation",
            }
        ),
        source_authorities={
            "base@1": ProfileSourceAuthority(
                source_ref="src_MEM-PROFILE-001",
                authority_tier=AuthorityTier.PROJECT_CONTROL,
            ),
            "software-engineering@1": ProfileSourceAuthority(
                source_ref="src_MEM-PROFILE-SE-001",
                authority_tier=AuthorityTier.PROJECT_CONTROL,
            ),
        },
    )
    registrations = load_profile_registry(
        PRODUCT_ROOT / "registries/memory_profile_registry.csv"
    )
    validate_profile_registrations(profiles, registrations)
    source_template = next(
        entry
        for entry in load_source_registry(
            PRODUCT_ROOT / "registries/memory_source_registry.csv"
        )
        if entry.source_id == "src_MEM-CODE-001"
    )
    source = replace(
        source_template,
        source_id="src_software-profile-proof",
        path_or_uri="src/example.py",
        path_pattern=None,
        source_kind="file",
        registry_path=None,
        row_number=None,
    )
    bundle = RegistryBundle(
        sources=(source,),
        profiles=registrations,
        relations=load_relation_registry(
            PRODUCT_ROOT / "registries/memory_relation_registry.csv"
        ),
    )
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
    )
    _initialize_provider(provider)
    components = ServiceComponents()
    service, audit, permission_path = _service(root, components=components)
    _install_agent_permissions(permission_path)
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    authorization = AuthorizationService(
        CanonicalPermissionEnvelopeLoader(
            boundary,
            "control_records/memory/permissions.json",
        )
    )
    operation_catalog_before = tuple(PUBLIC_OPERATION_CATALOG)

    with ExactIndex(":memory:") as index:
        components.registry_loader = lambda: bundle
        components.synchronizer = IngestionSynchronizer(
            project_root=root,
            index_writer=index,
            profile_set=profiles,
            optional_adapters=(SoftwareEngineeringPythonAdapter(),),
        )
        components.provider = provider
        components.retrieval = RetrievalEngine(
            project_id=PROJECT_ID,
            dataset_id=DATASET_ID,
            authorizer=authorization,
            exact_backend=index,
            exact_record_resolver=index,
            provider=provider,
        )
        synchronized = MemoryClient(
            service,
            identity=_identity(),
            project_id=PROJECT_ID,
            dataset_id=DATASET_ID,
        ).sync(
            source_ids=(source.source_id,),
            idempotency_key="software-profile-sync",
            request_id="mrq_software_profile_sync",
            trace_id="trace_software_profile_sync",
        )
        assert isinstance(synchronized, DispatchSuccess)
        assert synchronized.result["failure_count"] == 0

        records = index.current_source_records(
            project_id=PROJECT_ID,
            source_id=source.source_id,
        )
        assert {record.record_type for record in records} >= {
            "BuildTarget",
            "CodeSymbol",
            "FailurePattern",
            "TestCase",
        }
        results: list[RetrievalResult] = []
        for principal_id in ("agent-alpha", "agent-beta"):
            response = _agent_client(service, principal_id).recall(
                "parse payload",
                mode=RetrievalMode.SEMANTIC,
                request_id=f"mrq_software_profile_recall_{principal_id}",
                trace_id=f"trace_software_profile_recall_{principal_id}",
            )
            assert isinstance(response, DispatchSuccess)
            results.append(RetrievalResult.model_validate(response.result["retrieval"]))

        assert results[0].results
        assert results[1].results
        assert results[0].results[0].record_id == results[1].results[0].record_id
        assert results[0].results[0].record_type in {"CodeSymbol", "TestCase"}

    assert tuple(PUBLIC_OPERATION_CATALOG) == operation_catalog_before
    assert [event.outcome for event in audit.events()].count("failed") == 0
    assert not (root / ".sys4ai").exists()


@pytest.mark.parametrize(
    ("mutation", "expected_stage"),
    [
        ("missing_profile", "profile_selection"),
        ("undeclared_adapter", "profile_selection"),
        ("undeclared_record_type", "profile_validation"),
    ],
)
def test_profile_bound_sync_rejects_unregistered_runtime_material(
    tmp_path: Path,
    mutation: str,
    expected_stage: str,
) -> None:
    root = tmp_path.resolve()
    (root / "domain").mkdir()
    (root / "domain/widget.domain").write_text(
        "Calibration widget torque procedure.\n",
        encoding="utf-8",
    )
    profiles = _profile_set(root)
    entry = _source_entry()
    adapter: _DomainAdapter = _DomainAdapter()
    if mutation == "missing_profile":
        entry = replace(entry, profile_id="missing-profile@1")
    elif mutation == "undeclared_adapter":
        entry = replace(entry, ingestion_adapter="undeclared-domain@1")
    else:
        adapter = _UndeclaredRecordAdapter()

    result = IngestionSynchronizer(
        project_root=root,
        profile_set=profiles,
        optional_adapters=(adapter,),
    ).synchronize(_discovery(root, entry))

    assert not result.documents
    assert len(result.failures) == 1
    failure = result.failures[0]
    assert failure.category is ErrorCategory.PROFILE_INCOMPATIBLE
    assert failure.stage == expected_stage
    assert failure.source_id == entry.source_id
