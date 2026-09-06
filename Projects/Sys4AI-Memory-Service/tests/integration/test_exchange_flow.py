from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from sys4ai_memory.authorization import (
    AuthorizationService,
    CanonicalPermissionEnvelopeLoader,
)
from sys4ai_memory.contracts import (
    ErrorCategory,
    ErrorEnvelope,
    MemoryScope,
    ScopeReference,
    Sensitivity,
)
from sys4ai_memory.exchange import (
    AgeTool,
    ExportPolicy,
    MemoryPackageExporter,
    MemoryPackageImporter,
    PackageContainer,
)
from sys4ai_memory.interfaces import DispatchSuccess, MemoryClient
from sys4ai_memory.providers import (
    ExportRequest,
    ExportResult,
    InMemoryProviderConfig,
    ProviderContext,
    ProviderInitializationRequest,
    ProviderMutation,
    ProviderSnapshot,
    RememberRequest,
)
from sys4ai_memory.providers.in_memory import InMemoryProvider
from sys4ai_memory.security import ProjectBoundary
from sys4ai_memory.service import (
    DisposableMemoryPackageExchange,
    MemoryPackageExchange,
    ProviderAuthorizationBridge,
    ServiceComponents,
)
from tests.exchange.test_memory_package import _export_policy, _import_policy, _snapshot
from tests.providers.helpers import policy
from tests.service.test_dispatcher import DATASET_ID, PROJECT_ID, _identity, _service

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.acceptance]
AGE = shutil.which("age")
AGE_KEYGEN = shutil.which("age-keygen")


def _service_snapshot() -> ProviderSnapshot:
    source = _snapshot()
    sources = tuple(
        item.model_copy(
            update={
                "project_id": PROJECT_ID,
                "scope": ScopeReference(level=MemoryScope.PROJECT, scope_id=PROJECT_ID),
            }
        )
        for item in source.sources
    )
    records = tuple(
        item.model_copy(
            update={
                "project_id": PROJECT_ID,
                "scope": ScopeReference(level=MemoryScope.PROJECT, scope_id=PROJECT_ID),
            }
        )
        for item in source.records
    )
    relations = tuple(
        item.model_copy(update={"project_id": PROJECT_ID}) for item in source.relations
    )
    return ProviderSnapshot.build(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        created_at=source.created_at,
        origin_provider=source.origin_provider,
        origin_provider_version=source.origin_provider_version,
        profile_versions=dict(source.profile_versions),
        sources=sources,
        records=records,
        relations=relations,
    )


def _provider_context(trace_id: str) -> ProviderContext:
    return ProviderContext(
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
        principal_id=_identity().principal_id,
        scope=ScopeReference(level=MemoryScope.PROJECT, scope_id=PROJECT_ID),
        trace_id=trace_id,
    )


def _initialize_provider(
    provider: InMemoryProvider,
    *,
    snapshot: ProviderSnapshot | None = None,
) -> None:
    context = _provider_context("trace_exchange_provider_setup")

    async def initialize() -> None:
        await provider.initialize(
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
        if snapshot is not None:
            await provider.remember(
                RememberRequest(
                    context=context,
                    request_id="mrq_exchange_seed",
                    idempotency_key="exchange-seed",
                    sources=snapshot.sources,
                    records=snapshot.records,
                    relations=snapshot.relations,
                    authorization=policy(ProviderMutation.REMEMBER, context),
                )
            )

    asyncio.run(initialize())


def _attach_disposable_exchange(
    root: Path,
    provider: InMemoryProvider,
    components: ServiceComponents,
    *,
    import_stage_provider: InMemoryProvider | None = None,
) -> DisposableMemoryPackageExchange:
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    loader = CanonicalPermissionEnvelopeLoader(
        boundary,
        "control_records/memory/permissions.json",
    )
    authorization = AuthorizationService(loader)
    provider_authorization = ProviderAuthorizationBridge(authorization, loader)
    export_root = root / "exports"
    export_root.mkdir()
    import_policy = _import_policy().model_copy(
        update={"target_project_id": PROJECT_ID, "target_dataset_id": DATASET_ID}
    )
    exchange = DisposableMemoryPackageExchange(
        boundary=boundary,
        provider=provider,
        import_stage_provider=import_stage_provider,
        authorization=authorization,
        provider_authorization=provider_authorization,
        exporter=MemoryPackageExporter(disposable_root=export_root),
        importer=MemoryPackageImporter(
            boundary=boundary,
            derived_root=".sys4ai/memory",
            policy=import_policy,
        ),
        export_policy=_export_policy(allow_test=True),
        profile_versions={"base@1": "1.0.0"},
        container=PackageContainer.ZIP,
    )
    components.exchange = exchange
    return exchange


def test_public_export_rejects_a_mismatched_provider_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path.resolve()
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
    )
    _initialize_provider(provider, snapshot=_service_snapshot())
    components = ServiceComponents()
    service, audit, _ = _service(root, components=components)
    _attach_disposable_exchange(root, provider, components)
    original_export = provider.export

    async def mismatched_export(request: ExportRequest) -> ExportResult:
        result = await original_export(request)
        return result.model_copy(update={"request_id": "mrq_mismatched_provider_export"})

    monkeypatch.setattr(provider, "export", mismatched_export)
    response = MemoryClient(
        service,
        identity=_identity(),
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    ).export(
        "exports/must-not-exist.zip",
        idempotency_key="mismatched-provider-export",
        request_id="mrq_expected_provider_export",
        trace_id="trace_expected_provider_export",
    )

    assert isinstance(response, ErrorEnvelope)
    assert response.error.category is ErrorCategory.EXPORT_FAILED
    assert not (root / "exports/must-not-exist.zip").exists()
    assert [event.outcome for event in audit.events()] == ["authorized", "failed"]


@pytest.mark.skipif(AGE is None or AGE_KEYGEN is None, reason="age tooling is unavailable")
def test_public_export_uses_the_approved_age_envelope_for_sensitive_content(
    tmp_path: Path,
) -> None:
    assert AGE is not None
    assert AGE_KEYGEN is not None
    root = tmp_path.resolve()
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
    )
    _initialize_provider(provider, snapshot=_service_snapshot())
    components = ServiceComponents()
    service, audit, permission_path = _service(root, components=components)
    boundary = ProjectBoundary(PROJECT_ID, DATASET_ID, root)
    loader = CanonicalPermissionEnvelopeLoader(
        boundary,
        "control_records/memory/permissions.json",
    )
    authorization = AuthorizationService(loader)
    identity_file = root / "test-identity.txt"
    subprocess.run(  # noqa: S603 - resolved executable and disposable test identity
        (AGE_KEYGEN, "-o", str(identity_file)),
        capture_output=True,
        check=True,
    )
    recipient_result = subprocess.run(  # noqa: S603 - resolved executable
        (AGE_KEYGEN, "-y", str(identity_file)),
        capture_output=True,
        check=True,
        text=True,
    )
    recipient = recipient_result.stdout.strip()
    export_root = root / "exports"
    export_root.mkdir()
    age_tool = AgeTool(AGE)
    import_policy = _import_policy().model_copy(
        update={
            "target_project_id": PROJECT_ID,
            "target_dataset_id": DATASET_ID,
            "allowed_sensitivities": frozenset(
                {
                    Sensitivity.PUBLIC,
                    Sensitivity.INTERNAL,
                    Sensitivity.CONFIDENTIAL,
                    Sensitivity.RESTRICTED,
                }
            ),
            "required_encryption": "age-x25519",
            "allow_unencrypted_disposable_test_only": False,
        }
    )
    importer = MemoryPackageImporter(
        boundary=boundary,
        derived_root=".sys4ai/memory",
        policy=import_policy,
        age_tool=age_tool,
        identity_file=identity_file,
    )
    components.exchange = MemoryPackageExchange(
        boundary=boundary,
        provider=provider,
        authorization=authorization,
        provider_authorization=ProviderAuthorizationBridge(authorization, loader),
        exporter=MemoryPackageExporter(disposable_root=export_root, age_tool=age_tool),
        importer=importer,
        export_policy=ExportPolicy(
            format_decision_status="approved-provider-neutral-zip-json-jsonl@1",
            approved_encryption="age-x25519",
            allowed_sensitivities=import_policy.allowed_sensitivities,
        ),
        profile_versions={"base@1": "1.0.0"},
        container=PackageContainer.ZIP,
    )

    package_path = root / "exports/memory.zip.age"
    response = MemoryClient(
        service,
        identity=_identity(),
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    ).export(
        "exports/memory.zip.age",
        include_sensitive=True,
        age_recipient=recipient,
        idempotency_key="approved-age-export",
        request_id="mrq_approved_age_export",
        trace_id="trace_approved_age_export",
    )

    assert isinstance(response, DispatchSuccess)
    assert response.result["production_ready"] is True
    assert not zipfile.is_zipfile(package_path)
    assert b"mem_RESTRICTED" not in package_path.read_bytes()
    validated = importer.validator.validate(package_path)
    assert validated.manifest.encryption == "age-x25519"
    assert {record.record_id for record in validated.snapshot.records} >= {
        "mem_ALPHA",
        "mem_RESTRICTED",
    }
    assert [event.outcome for event in audit.events()] == ["authorized", "succeeded"]
    assert permission_path.is_file()


def test_public_disposable_export_preview_and_import_round_trip(tmp_path: Path) -> None:
    source_root = (tmp_path / "source-project").resolve()
    target_root = (tmp_path / "target-project").resolve()
    source_root.mkdir()
    target_root.mkdir()

    source_provider = InMemoryProvider(
        InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
    )
    target_provider = InMemoryProvider(
        InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
    )
    target_stage_provider = InMemoryProvider(
        InMemoryProviderConfig(project_id=PROJECT_ID, dataset_id=DATASET_ID)
    )
    _initialize_provider(source_provider, snapshot=_service_snapshot())
    _initialize_provider(target_provider)
    _initialize_provider(target_stage_provider)

    source_components = ServiceComponents()
    target_components = ServiceComponents()
    source_service, source_audit, _ = _service(source_root, components=source_components)
    target_service, target_audit, _ = _service(target_root, components=target_components)
    _attach_disposable_exchange(source_root, source_provider, source_components)
    _attach_disposable_exchange(
        target_root,
        target_provider,
        target_components,
        import_stage_provider=target_stage_provider,
    )

    canonical = target_root / "PRDs/Sys4AI_Memory_Service_PRD.md"
    canonical.parent.mkdir()
    canonical.write_text("canonical target remains unchanged\n", encoding="utf-8")
    canonical_before = canonical.read_bytes()
    identity = _identity()
    source_client = MemoryClient(
        source_service,
        identity=identity,
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    )
    exported = source_client.export(
        "exports/memory.zip",
        idempotency_key="public-exchange-export",
        request_id="mrq_public_exchange_export",
        trace_id="trace_public_exchange_export",
    )
    assert isinstance(exported, DispatchSuccess)
    assert exported.result["production_ready"] is False
    candidate = exported.result["candidate"]
    assert isinstance(candidate, dict)
    source_package = source_root / "exports/memory.zip"
    with zipfile.ZipFile(source_package) as archive:
        assert "manifest.json" in archive.namelist()
        assert "records.jsonl" in archive.namelist()

    target_imports = target_root / "imports"
    target_imports.mkdir()
    target_package = target_imports / "memory.zip"
    shutil.copyfile(source_package, target_package)
    target_client = MemoryClient(
        target_service,
        identity=identity,
        project_id=PROJECT_ID,
        dataset_id=DATASET_ID,
    )
    previewed = target_client.import_package(
        "imports/memory.zip",
        idempotency_key="public-exchange-preview",
        expected_sha256=candidate["manifest"]["package_sha256"],
        request_id="mrq_public_exchange_preview",
        trace_id="trace_public_exchange_preview",
    )
    assert isinstance(previewed, DispatchSuccess)
    assert previewed.result["production_ready"] is False
    preview = previewed.result["preview"]
    assert isinstance(preview, dict)

    activated = target_client.import_package(
        "imports/memory.zip",
        idempotency_key="public-exchange-activate",
        activate=True,
        expected_sha256=candidate["manifest"]["package_sha256"],
        impact_digest=preview["impact_digest"],
        request_id="mrq_public_exchange_activate",
        trace_id="trace_public_exchange_activate",
    )
    assert isinstance(activated, DispatchSuccess)
    assert activated.result["production_ready"] is False
    receipt = activated.result["receipt"]
    assert isinstance(receipt, dict)
    assert set(receipt["imported_record_ids"]) == {"mem_ALPHA", "mem_BETA"}
    assert receipt["imported_relation_ids"] == ["rel_ALPHA_DEPENDS_ON_BETA"]
    assert canonical.read_bytes() == canonical_before
    assert (target_root / ".sys4ai/memory/active-import.json").is_file()

    export_context = _provider_context("trace_public_exchange_old_provider")
    old_provider_export = asyncio.run(
        target_provider.export(
            ExportRequest(
                context=export_context,
                request_id="mrq_public_exchange_old_provider",
                idempotency_key="public-exchange-old-provider",
                profile_versions={"base@1": "1.0.0"},
                authorization=policy(ProviderMutation.EXPORT, export_context),
            )
        )
    )
    assert old_provider_export.record_count == 0
    reexported = target_client.export(
        "exports/imported-memory.zip",
        idempotency_key="public-exchange-reexport",
        request_id="mrq_public_exchange_reexport",
        trace_id="trace_public_exchange_reexport",
    )
    assert isinstance(reexported, DispatchSuccess)
    with zipfile.ZipFile(target_root / "exports/imported-memory.zip") as archive:
        imported_records = {
            line["record_id"]
            for line in (
                json.loads(raw)
                for raw in archive.read("records.jsonl").decode("utf-8").splitlines()
            )
        }
    assert imported_records == {"mem_ALPHA", "mem_BETA"}
    assert [event.outcome for event in source_audit.events()] == ["authorized", "succeeded"]
    assert [event.outcome for event in target_audit.events()] == [
        "authorized",
        "succeeded",
        "authorized",
        "succeeded",
        "authorized",
        "succeeded",
    ]
