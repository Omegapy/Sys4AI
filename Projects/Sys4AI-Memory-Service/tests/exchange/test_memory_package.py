from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sys4ai_memory.authorization import AuthorizationDecision
from sys4ai_memory.contracts import Permission, RetrievalMode, Sensitivity, TrustClass
from sys4ai_memory.contracts.models import MemoryRecord, RelationRecord, SourceRecord
from sys4ai_memory.exchange import (
    AgeTool,
    AuthorizedExchangeImpact,
    ExchangePolicyError,
    ExportPolicy,
    ImportConflictError,
    ImportPolicy,
    MemoryPackageExporter,
    MemoryPackageImporter,
    MemoryPackageValidator,
    MigrationRegistry,
    MigrationStep,
    PackageContainer,
    PackageValidationError,
    ProviderImportStage,
    plan_cogx_delegation,
)
from sys4ai_memory.providers import (
    IN_MEMORY_PROVIDER_VERSION,
    CogneeProviderConfig,
    ExportRequest,
    ImportRequest,
    ImportResult,
    InMemoryProviderConfig,
    ProviderInitializationRequest,
    ProviderMutation,
    ProviderName,
    ProviderSnapshot,
    RecallRequest,
)
from sys4ai_memory.providers.cognee import CogneeProvider
from sys4ai_memory.providers.in_memory import InMemoryProvider
from sys4ai_memory.security.isolation import ProjectBoundary
from sys4ai_memory.util import canonical_json_bytes, sha256_bytes
from tests.providers.helpers import (
    SHA_C,
    context,
    memory_record,
    policy,
    relation_record,
    source_record,
)
from tests.providers.test_cognee import FakeCogneeRuntime

NOW = datetime(2026, 9, 3, 12, tzinfo=UTC)
CONFIGURATION_SHA = SHA_C
SAFE_SOURCE_SHA = "a" * 64
AGE = shutil.which("age")
AGE_KEYGEN = shutil.which("age-keygen")


def _sensitive_source_and_record() -> tuple[SourceRecord, MemoryRecord]:
    source_value = source_record().to_json_dict()
    source_value.update(
        {
            "source_id": "src_restricted",
            "path_or_uri": "private/restricted.txt",
            "sensitivity": "restricted",
            "content_sha256": "e" * 64,
            "locator": {"path": "private/restricted.txt"},
        }
    )
    source = SourceRecord.model_validate(source_value)
    record_value = memory_record("mem_RESTRICTED").to_json_dict()
    record_value["source"].update(
        {
            "source_id": source.source_id,
            "path": source.path_or_uri,
            "content_sha256": source.content_sha256,
            "locator": {"path": source.path_or_uri},
        }
    )
    record_value["security"]["sensitivity"] = "restricted"
    record_value["content"]["exact"] = "restricted fixture content"
    return source, MemoryRecord.model_validate(record_value)


def _snapshot() -> ProviderSnapshot:
    safe_source_value = source_record().to_json_dict()
    safe_source_value["content_sha256"] = SAFE_SOURCE_SHA
    safe_source = SourceRecord.model_validate(safe_source_value)
    alpha = memory_record("mem_ALPHA", title="Alpha", exact="portable alpha evidence")
    beta = memory_record("mem_BETA", title="Beta", exact="portable beta evidence")
    relation_value = relation_record("mem_ALPHA", "mem_BETA").to_json_dict()
    relation_value["source"] = {
        "source_id": safe_source.source_id,
        "locator": {"path": safe_source.path_or_uri},
    }
    relation = RelationRecord.model_validate(relation_value)
    sensitive_source, sensitive_record = _sensitive_source_and_record()
    return ProviderSnapshot.build(
        project_id="project-alpha",
        dataset_id="project-alpha-memory",
        created_at=NOW,
        origin_provider=ProviderName.IN_MEMORY,
        origin_provider_version=IN_MEMORY_PROVIDER_VERSION,
        profile_versions={"base@1": "1.0.0"},
        sources=(safe_source, sensitive_source),
        records=(alpha, beta, sensitive_record),
        relations=(relation,),
    )


def _export_policy(*, allow_test: bool) -> ExportPolicy:
    return ExportPolicy(
        format_decision_status="pending-user-decision",
        encryption_required=True,
        approved_encryption=None,
        allowed_sensitivities=frozenset({Sensitivity.PUBLIC, Sensitivity.INTERNAL}),
        allow_unencrypted_disposable_test_only=allow_test,
    )


def _import_policy(
    *,
    project_id: str = "project-alpha",
    canonical_hash: str = SAFE_SOURCE_SHA,
    max_compression_ratio: float = 50.0,
) -> ImportPolicy:
    return ImportPolicy(
        target_project_id=project_id,
        target_dataset_id=f"{project_id}-memory",
        expected_profile_versions={"base@1": "1.0.0"},
        allowed_trust_classes=frozenset({TrustClass.HUMAN_APPROVED, TrustClass.PROJECT_AUTHORED}),
        allowed_sensitivities=frozenset({Sensitivity.PUBLIC, Sensitivity.INTERNAL}),
        canonical_source_hashes={"src_prd_memory": canonical_hash},
        canonical_path_hashes={
            "PRDs/Sys4AI_Memory_Service_PRD.md": canonical_hash,
        },
        max_compression_ratio=max_compression_ratio,
        allow_unencrypted_disposable_test_only=True,
    )


def _export(
    tmp_path: Path,
    *,
    container: PackageContainer = PackageContainer.DIRECTORY,
    name: str = "candidate",
) -> Path:
    export_root = tmp_path / "exports"
    export_root.mkdir(exist_ok=True)
    destination = export_root / name
    MemoryPackageExporter(disposable_root=export_root.resolve()).export_snapshot(
        _snapshot(),
        destination=destination,
        container=container,
        policy=_export_policy(allow_test=True),
        disposable_test_only=True,
    )
    return destination


def _exchange_authorization(digest: str) -> AuthorizedExchangeImpact:
    return AuthorizedExchangeImpact(
        decision=AuthorizationDecision(
            allowed=True,
            reason_code="allowed",
            principal_id="admin_fixture",
            project_id="project-alpha",
            dataset_id="project-alpha-memory",
            operation="memory.import.activate",
            permission=Permission.ADMINISTER,
            permission_revision="revision-1",
            canonical_sha256="a" * 64,
            grant_id="grant-import",
        ),
        impact_digest=digest,
    )


def test_import_stage_rejects_the_active_provider_instance() -> None:
    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )
    provider_context = context("project-alpha", "project-alpha-memory")
    with pytest.raises(ValueError, match="distinct from the active provider"):
        ProviderImportStage(
            provider=provider,
            active_provider=provider,
            context=provider_context,
            preview_authorization=policy(ProviderMutation.IMPORT, provider_context),
        )


async def _initialized_provider() -> tuple[InMemoryProvider, ProviderImportStage]:
    provider = InMemoryProvider(
        InMemoryProviderConfig(
            project_id="project-alpha",
            dataset_id="project-alpha-memory",
        )
    )
    active_provider = InMemoryProvider(
        InMemoryProviderConfig(
            project_id="project-alpha",
            dataset_id="project-alpha-memory",
        )
    )
    provider_context = context(
        "project-alpha",
        "project-alpha-memory",
        trace_id="trace_exchange_roundtrip",
    )
    for candidate in (provider, active_provider):
        await candidate.initialize(
            ProviderInitializationRequest(
                context=provider_context,
                configuration_fingerprint=CONFIGURATION_SHA,
                dry_run=False,
                path_boundaries_validated=True,
                exclusions_validated=True,
                discovery_dry_run_approved=True,
                authorization=policy(ProviderMutation.INITIALIZE, provider_context),
            )
        )
    return provider, ProviderImportStage(
        provider=provider,
        active_provider=active_provider,
        context=provider_context,
        preview_authorization=policy(ProviderMutation.IMPORT, provider_context),
    )


def test_normal_export_is_denied_and_test_candidate_filters_sensitivity(
    tmp_path: Path,
) -> None:
    export_root = (tmp_path / "exports").resolve()
    export_root.mkdir()
    exporter = MemoryPackageExporter(disposable_root=export_root)
    with pytest.raises(ExchangePolicyError, match="archive/encryption"):
        exporter.export_snapshot(
            _snapshot(),
            destination=export_root / "denied",
            container=PackageContainer.DIRECTORY,
            policy=_export_policy(allow_test=False),
        )

    candidate = exporter.export_snapshot(
        _snapshot(),
        destination=export_root / "allowed-test-candidate",
        container=PackageContainer.DIRECTORY,
        policy=_export_policy(allow_test=True),
        disposable_test_only=True,
    )
    assert candidate.excluded_record_ids == ("mem_RESTRICTED",)
    assert candidate.excluded_source_ids == ("src_restricted",)
    assert (Path(candidate.destination) / "manifest.json").is_file()
    manifest = json.loads(
        (Path(candidate.destination) / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["encryption"] == "unresolved-test-only-none"
    assert manifest["disposable_test_only"] is True
    records = (Path(candidate.destination) / "records.jsonl").read_text(encoding="utf-8")
    assert "mem_ALPHA" in records
    assert "mem_RESTRICTED" not in records
    assert all(
        not item["package_included"]
        for item in manifest["backup_assets"]
        if item["asset_class"] in {"canonical", "sensitive"}
    )


def test_unencrypted_candidate_rejects_secret_like_content(tmp_path: Path) -> None:
    snapshot = _snapshot()
    secret = memory_record(
        "mem_SECRET_PATTERN",
        summary="api_key=runtime-generated-secret-value",
    )
    unsafe_snapshot = ProviderSnapshot.build(
        project_id=snapshot.project_id,
        dataset_id=snapshot.dataset_id,
        created_at=snapshot.created_at,
        origin_provider=snapshot.origin_provider,
        origin_provider_version=snapshot.origin_provider_version,
        profile_versions=dict(snapshot.profile_versions),
        sources=snapshot.sources,
        records=(*snapshot.records, secret),
        relations=snapshot.relations,
    )
    export_root = (tmp_path / "exports").resolve()
    export_root.mkdir()
    with pytest.raises(ExchangePolicyError, match="secret-like content"):
        MemoryPackageExporter(disposable_root=export_root).export_snapshot(
            unsafe_snapshot,
            destination=export_root / "secret-rejected",
            container=PackageContainer.DIRECTORY,
            policy=_export_policy(allow_test=True),
            disposable_test_only=True,
        )


def test_directory_and_zip_are_deterministic_and_inspectable(tmp_path: Path) -> None:
    directory = _export(tmp_path, name="candidate-directory")
    zip_one = _export(
        tmp_path,
        container=PackageContainer.ZIP,
        name="candidate-one.zip",
    )
    zip_two = _export(
        tmp_path,
        container=PackageContainer.ZIP,
        name="candidate-two.zip",
    )
    validator = MemoryPackageValidator(_import_policy())

    directory_package = validator.validate(directory)
    zip_package = validator.validate(zip_one)
    assert directory_package.manifest.package_sha256 == zip_package.manifest.package_sha256
    assert zip_one.read_bytes() == zip_two.read_bytes()
    assert {item.record_id for item in zip_package.snapshot.records} == {
        "mem_ALPHA",
        "mem_BETA",
    }
    with zipfile.ZipFile(zip_one) as archive:
        assert set(archive.namelist()) == {
            "backup-assets.json",
            "manifest.json",
            "profiles.json",
            "provenance.jsonl",
            "records.jsonl",
            "relations.jsonl",
            "sources.jsonl",
            "status.json",
        }


@pytest.mark.skipif(AGE is None or AGE_KEYGEN is None, reason="age tooling is unavailable")
def test_age_envelope_round_trip_includes_non_public_content_without_key_persistence(
    tmp_path: Path,
) -> None:
    assert AGE is not None
    assert AGE_KEYGEN is not None
    identity = tmp_path / "identity.txt"
    generated = subprocess.run(  # noqa: S603 - resolved test executable and disposable output
        (AGE_KEYGEN, "-o", str(identity)),
        capture_output=True,
        check=True,
    )
    assert generated.returncode == 0
    recipient_result = subprocess.run(  # noqa: S603 - resolved test executable
        (AGE_KEYGEN, "-y", str(identity)),
        capture_output=True,
        check=True,
        text=True,
    )
    recipient = recipient_result.stdout.strip()
    export_root = (tmp_path / "exports").resolve()
    export_root.mkdir()
    age_tool = AgeTool(AGE)
    policy = ExportPolicy(
        format_decision_status="approved-provider-neutral-zip-json-jsonl@1",
        approved_encryption="age-x25519",
        allowed_sensitivities=frozenset(
            {
                Sensitivity.PUBLIC,
                Sensitivity.INTERNAL,
                Sensitivity.CONFIDENTIAL,
                Sensitivity.RESTRICTED,
            }
        ),
    )
    first_path = export_root / "memory-one.zip.age"
    second_path = export_root / "memory-two.zip.age"
    exporter = MemoryPackageExporter(disposable_root=export_root, age_tool=age_tool)
    first = exporter.export_snapshot(
        _snapshot(),
        destination=first_path,
        container=PackageContainer.ZIP,
        policy=policy,
        age_recipient=recipient,
    )
    second = exporter.export_snapshot(
        _snapshot(),
        destination=second_path,
        container=PackageContainer.ZIP,
        policy=policy,
        age_recipient=recipient,
    )

    assert age_tool.version().startswith("v1.")
    assert first.manifest.encryption == "age-x25519"
    assert first.manifest.disposable_test_only is False
    assert first.excluded_record_ids == ()
    assert first.manifest_sha256 == second.manifest_sha256
    assert not zipfile.is_zipfile(first_path)
    assert b"mem_RESTRICTED" not in first_path.read_bytes()
    first_plaintext = age_tool.decrypt(
        first_path.read_bytes(),
        identity_file=identity,
        max_output_bytes=8 * 1024 * 1024,
    )
    second_plaintext = age_tool.decrypt(
        second_path.read_bytes(),
        identity_file=identity,
        max_output_bytes=8 * 1024 * 1024,
    )
    assert first_plaintext == second_plaintext

    import_policy = _import_policy().model_copy(
        update={
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
    validated = MemoryPackageValidator(
        import_policy,
        age_tool=age_tool,
        identity_file=identity,
    ).validate(first_path)
    assert {record.record_id for record in validated.snapshot.records} == {
        "mem_ALPHA",
        "mem_BETA",
        "mem_RESTRICTED",
    }

    wrong_identity = tmp_path / "wrong-identity.txt"
    subprocess.run(  # noqa: S603 - resolved test executable and disposable output
        (AGE_KEYGEN, "-o", str(wrong_identity)),
        capture_output=True,
        check=True,
    )
    with pytest.raises(PackageValidationError, match="age envelope decryption failed"):
        MemoryPackageValidator(
            import_policy,
            age_tool=age_tool,
            identity_file=wrong_identity,
        ).validate(first_path)


@pytest.mark.asyncio
async def test_round_trip_stages_and_activates_without_canonical_overwrite(
    tmp_path: Path,
) -> None:
    package = _export(tmp_path, name="round-trip-package")
    target = (tmp_path / "clean-project").resolve()
    canonical = target / "PRDs/Sys4AI_Memory_Service_PRD.md"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("canonical target remains unchanged\n", encoding="utf-8")
    before = canonical.read_bytes()
    boundary = ProjectBoundary(
        project_id="project-alpha",
        dataset_id="project-alpha-memory",
        root=target,
    )
    importer = MemoryPackageImporter(
        boundary=boundary,
        derived_root=".sys4ai/memory",
        policy=_import_policy(),
    )
    preview = importer.validator.preview(package)
    provider, provider_stage = await _initialized_provider()
    staged = await importer.stage(
        preview,
        authorization=_exchange_authorization(preview.impact_digest),
        provider_stage=provider_stage,
    )
    receipt = await importer.activate(
        staged,
        authorization=_exchange_authorization(preview.impact_digest),
        provider_stage=provider_stage,
        execution_authorization=policy(
            ProviderMutation.IMPORT,
            provider_stage.context,
            impact_digest=staged.provider_impact_digest,
        ),
    )

    assert set(receipt.imported_record_ids) == {"mem_ALPHA", "mem_BETA"}
    assert receipt.canonical_sources_overwritten is False
    assert canonical.read_bytes() == before
    assert (target / ".sys4ai/memory/active-import.json").is_file()
    provenance = (
        target / ".sys4ai/memory/imports" / receipt.package_id / "import-provenance.jsonl"
    ).read_text(encoding="utf-8")
    assert receipt.package_id in provenance
    assert "origin_provider" in provenance
    exported = await provider.export(
        ExportRequest(
            context=provider_stage.context,
            request_id="mrq_roundtrip_export",
            idempotency_key="roundtrip-export",
            profile_versions={"base@1": "1.0.0"},
            authorization=policy(ProviderMutation.EXPORT, provider_stage.context),
        )
    )
    assert exported.snapshot is not None
    assert {item.record_id for item in exported.snapshot.records} == {"mem_ALPHA", "mem_BETA"}


@pytest.mark.asyncio
async def test_provider_neutral_package_rebuilds_an_isolated_cognee_adapter(
    tmp_path: Path,
) -> None:
    real_cognee_was_loaded = "cognee" in sys.modules
    package = _export(tmp_path, name="cross-provider-package")
    target = (tmp_path / "cross-provider-target").resolve()
    target.mkdir()
    canonical = target / "PRDs/Sys4AI_Memory_Service_PRD.md"
    canonical.parent.mkdir()
    canonical.write_text("canonical target remains unchanged\n", encoding="utf-8")
    canonical_before = canonical.read_bytes()
    importer = MemoryPackageImporter(
        boundary=ProjectBoundary(
            project_id="project-alpha",
            dataset_id="project-alpha-memory",
            root=target,
        ),
        derived_root=".sys4ai/memory",
        policy=_import_policy(),
    )
    runtime = FakeCogneeRuntime()
    cognee = CogneeProvider(
        CogneeProviderConfig(
            project_id="project-alpha",
            dataset_id="project-alpha-memory",
            project_root=str(target),
            derived_data_root=str(target / ".sys4ai/memory/provider-stage"),
            semantic_enabled=True,
            llm_provider="ollama",
            llm_model="local-test-model",
            llm_endpoint="http://127.0.0.1:11434",
            embedding_provider="fastembed",
            embedding_model="local-test-embedding",
            embedding_dimensions=384,
        ),
        runtime=runtime,
    )
    provider_context = context(
        "project-alpha",
        "project-alpha-memory",
        trace_id="trace_cross_provider_import",
    )
    await cognee.initialize(
        ProviderInitializationRequest(
            context=provider_context,
            configuration_fingerprint=CONFIGURATION_SHA,
            dry_run=False,
            path_boundaries_validated=True,
            exclusions_validated=True,
            discovery_dry_run_approved=True,
            authorization=policy(ProviderMutation.INITIALIZE, provider_context),
        )
    )
    _, inactive_stage = await _initialized_provider()
    provider_stage = ProviderImportStage(
        provider=cognee,
        active_provider=inactive_stage.active_provider,
        context=provider_context,
        preview_authorization=policy(ProviderMutation.IMPORT, provider_context),
    )
    preview = importer.validator.preview(package)
    staged = await importer.stage(
        preview,
        authorization=_exchange_authorization(preview.impact_digest),
        provider_stage=provider_stage,
    )
    receipt = await importer.activate(
        staged,
        authorization=_exchange_authorization(preview.impact_digest),
        provider_stage=provider_stage,
        execution_authorization=policy(
            ProviderMutation.IMPORT,
            provider_context,
            impact_digest=staged.provider_impact_digest,
        ),
    )

    assert set(receipt.imported_record_ids) == {"mem_ALPHA", "mem_BETA"}
    assert receipt.imported_relation_ids == ("rel_ALPHA_DEPENDS_ON_BETA",)
    assert runtime.calls == ["configure", "remember"]
    assert canonical.read_bytes() == canonical_before
    runtime.recall_result = [
        {"score": 0.92, "external_metadata": item.external_metadata}
        for item in runtime.items
    ]
    recalled = await cognee.recall(
        RecallRequest(
            context=provider_context,
            request_id="mrq_cross_provider_recall",
            query="portable evidence",
            mode=RetrievalMode.SEMANTIC,
        )
    )
    assert {item.record.record_id for item in recalled.candidates} == {
        "mem_ALPHA",
        "mem_BETA",
    }
    assert tuple(item.relation_id for item in recalled.relations) == (
        "rel_ALPHA_DEPENDS_ON_BETA",
    )
    assert ("cognee" in sys.modules) is real_cognee_was_loaded


@pytest.mark.asyncio
async def test_import_authorization_must_match_exact_preview(tmp_path: Path) -> None:
    package = _export(tmp_path, name="authorization-package")
    target = (tmp_path / "authorization-target").resolve()
    target.mkdir()
    importer = MemoryPackageImporter(
        boundary=ProjectBoundary(
            project_id="project-alpha",
            dataset_id="project-alpha-memory",
            root=target,
        ),
        derived_root=".sys4ai/memory",
        policy=_import_policy(),
    )
    preview = importer.validator.preview(package)
    _, provider_stage = await _initialized_provider()

    with pytest.raises(ExchangePolicyError, match="does not match preview"):
        await importer.stage(
            preview,
            authorization=_exchange_authorization("b" * 64),
            provider_stage=provider_stage,
        )
    assert not (target / ".sys4ai").exists()


def test_tamper_scope_and_canonical_conflict_are_rejected(tmp_path: Path) -> None:
    package = _export(tmp_path, name="tamper-package")
    validator = MemoryPackageValidator(_import_policy())
    (package / "records.jsonl").write_bytes((package / "records.jsonl").read_bytes() + b"{}\n")
    with pytest.raises(PackageValidationError, match="checksum"):
        validator.validate(package)

    clean_package = _export(tmp_path, name="scope-package")
    with pytest.raises(ImportConflictError, match="project or dataset"):
        MemoryPackageValidator(_import_policy(project_id="project-beta")).validate(clean_package)
    with pytest.raises(ImportConflictError, match="canonical metadata"):
        MemoryPackageValidator(_import_policy(canonical_hash="b" * 64)).validate(clean_package)
    incompatible = _import_policy().model_copy(
        update={"expected_profile_versions": {"base@1": "2.0.0"}}
    )
    with pytest.raises(ImportConflictError, match="profile versions"):
        MemoryPackageValidator(incompatible).validate(clean_package)
    disallowed_trust = _import_policy().model_copy(
        update={"allowed_trust_classes": frozenset({TrustClass.SYSTEM_CONTROLLED})}
    )
    with pytest.raises(PackageValidationError, match="trust or sensitivity"):
        MemoryPackageValidator(disallowed_trust).validate(clean_package)


def test_checksum_consistent_orphan_source_reference_fails_closed(tmp_path: Path) -> None:
    package = _export(tmp_path, name="orphan-source-package")
    records_path = package / "records.jsonl"
    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
    records[0]["source"]["source_id"] = "src_orphan"
    records_content = b"".join(canonical_json_bytes(record) for record in records)
    records_path.write_bytes(records_content)

    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records_metadata = next(item for item in manifest["files"] if item["path"] == "records.jsonl")
    records_metadata.update(
        {
            "byte_size": len(records_content),
            "item_count": len(records),
            "sha256": sha256_bytes(records_content),
        }
    )
    digest_payload = dict(manifest)
    digest_payload.pop("package_sha256")
    manifest["package_sha256"] = sha256_bytes(canonical_json_bytes(digest_payload))
    manifest_path.write_bytes(canonical_json_bytes(manifest))

    with pytest.raises(PackageValidationError, match="source metadata is missing"):
        MemoryPackageValidator(_import_policy()).validate(package)


@pytest.mark.asyncio
async def test_mismatched_provider_execution_result_never_activates_filesystem_pointer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _export(tmp_path, name="mismatched-provider-result")
    target = (tmp_path / "mismatched-provider-target").resolve()
    target.mkdir()
    importer = MemoryPackageImporter(
        boundary=ProjectBoundary(
            project_id="project-alpha",
            dataset_id="project-alpha-memory",
            root=target,
        ),
        derived_root=".sys4ai/memory",
        policy=_import_policy(),
    )
    preview = importer.validator.preview(package)
    provider, provider_stage = await _initialized_provider()
    staged = await importer.stage(
        preview,
        authorization=_exchange_authorization(preview.impact_digest),
        provider_stage=provider_stage,
    )
    original_import = provider.import_snapshot

    async def tampered_import(request: ImportRequest) -> ImportResult:
        result = await original_import(request)
        if result.executed:
            return result.model_copy(update={"request_id": "mrq_wrong_result"})
        return result

    monkeypatch.setattr(provider, "import_snapshot", tampered_import)
    with pytest.raises(ImportConflictError, match="provider import result"):
        await importer.activate(
            staged,
            authorization=_exchange_authorization(preview.impact_digest),
            provider_stage=provider_stage,
            execution_authorization=policy(
                ProviderMutation.IMPORT,
                provider_stage.context,
                impact_digest=staged.provider_impact_digest,
            ),
        )

    assert not (target / ".sys4ai/memory/active-import.json").exists()
    assert not (target / ".sys4ai/memory/imports" / staged.package_id).exists()
    active_export = await provider_stage.active_provider.export(
        ExportRequest(
            context=provider_stage.context,
            request_id="mrq_active_provider_unchanged",
            idempotency_key="active-provider-unchanged",
            profile_versions={"base@1": "1.0.0"},
            authorization=policy(ProviderMutation.EXPORT, provider_stage.context),
        )
    )
    staged_export = await provider.export(
        ExportRequest(
            context=provider_stage.context,
            request_id="mrq_failed_stage_diagnostic",
            idempotency_key="failed-stage-diagnostic",
            profile_versions={"base@1": "1.0.0"},
            authorization=policy(ProviderMutation.EXPORT, provider_stage.context),
        )
    )
    assert active_export.record_count == 0
    assert staged_export.record_count == 2


def test_zip_slip_duplicate_and_bomb_inputs_fail_before_extraction(tmp_path: Path) -> None:
    policy = _import_policy(max_compression_ratio=5.0)
    validator = MemoryPackageValidator(policy)
    slip = tmp_path / "slip.zip"
    with zipfile.ZipFile(slip, "w") as archive:
        archive.writestr("../manifest.json", "{}")
    with pytest.raises(PackageValidationError, match="unsafe member"):
        validator.validate(slip)

    duplicate = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(duplicate, "w") as archive:
        archive.writestr("manifest.json", "{}")
        archive.writestr("MANIFEST.JSON", "{}")
    with pytest.raises(PackageValidationError, match="duplicate"):
        validator.validate(duplicate)

    bomb = tmp_path / "bomb.zip"
    with zipfile.ZipFile(bomb, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", b"0" * 100_000)
    with pytest.raises(PackageValidationError, match="compression ratio"):
        validator.validate(bomb)


def test_versioned_migration_dry_run_and_cogx_policy_gate(tmp_path: Path) -> None:
    package = _export(tmp_path, name="migration-package")
    validated = MemoryPackageValidator(_import_policy()).validate(package)
    registry = MigrationRegistry(
        (
            MigrationStep(
                step_id="smp-1.0-to-1.1",
                source_version="1.0.0",
                target_version="1.1.0",
                description="example reviewed provider-neutral record transform",
            ),
        )
    )
    report = registry.dry_run(
        validated.manifest,
        target_version="1.1.0",
        record_ids=tuple(item.record_id for item in validated.snapshot.records),
    )
    assert not report.executed
    assert report.steps[0].step_id == "smp-1.0-to-1.1"
    assert set(report.affected_record_ids) == {"mem_ALPHA", "mem_BETA"}

    provider = InMemoryProvider(
        InMemoryProviderConfig(project_id="project-alpha", dataset_id="project-alpha-memory")
    )
    delegation = plan_cogx_delegation(
        provider,
        direction="export",
        artifact_path=".sys4ai/memory/exports/candidate.cogx",
        provider_native_enabled=False,
        format_decision_status="pending-user-decision",
    )
    assert delegation.provider_owned
    assert not delegation.approved
    assert delegation.reason_code == "provider_native_exchange_policy_disabled_or_unresolved"
