from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from sys4ai_memory.authorization import AuthorizationDecision
from sys4ai_memory.bootstrap import prepare_project_memory
from sys4ai_memory.configuration import load_configuration
from sys4ai_memory.contracts import Permission, RelationRecord
from sys4ai_memory.exact_index import ExactIndex
from sys4ai_memory.ingestion import IngestionSynchronizer, available_adapters
from sys4ai_memory.initialization import apply_initialization, build_initialization_preview
from sys4ai_memory.providers import (
    IN_MEMORY_PROVIDER_VERSION,
    InMemoryProviderConfig,
    ProviderInitializationRequest,
    ProviderMutation,
    ProviderSnapshot,
)
from sys4ai_memory.providers.in_memory import InMemoryProvider
from sys4ai_memory.rebuild import (
    AuthorizedRebuildImpact,
    GenerationRebuilder,
    ProviderStage,
    RebuildAuthorizationError,
    RebuildConflictError,
    RebuildError,
    RebuildMode,
    RebuildOutcome,
    RebuildStage,
)
from sys4ai_memory.security.isolation import ProjectBoundary
from sys4ai_memory.sources import RegistryBundle, SourceDiscovery, load_source_registry
from tests.providers.helpers import context, policy
from tests.retrieval.helpers import relation_record as retrieval_relation_record

FIXTURES = Path(__file__).parents[1] / "fixtures/projects/project_alpha"
CONFIG_SHA = "c" * 64
PROFILE_SHA = "d" * 64


def _canonical_snapshot(root: Path) -> dict[str, bytes]:
    """Capture every fixture source outside disposable derived storage."""

    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".sys4ai" not in path.relative_to(root).parts
    }


class InMemoryStageFactory:
    def __init__(self, *, project_id: str, dataset_id: str) -> None:
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.providers: dict[str, InMemoryProvider] = {}

    async def __call__(self, generation_root: Path, generation_id: str) -> ProviderStage:
        assert generation_root.parts[-1] == "provider"
        provider = InMemoryProvider(
            InMemoryProviderConfig(
                project_id=self.project_id,
                dataset_id=self.dataset_id,
            )
        )
        provider_context = context(
            self.project_id,
            self.dataset_id,
            trace_id=f"trace_{generation_id}",
        )
        await provider.initialize(
            ProviderInitializationRequest(
                context=provider_context,
                configuration_fingerprint=CONFIG_SHA,
                dry_run=False,
                path_boundaries_validated=True,
                exclusions_validated=True,
                discovery_dry_run_approved=True,
                authorization=policy(ProviderMutation.INITIALIZE, provider_context),
            )
        )
        self.providers[generation_id] = provider
        return ProviderStage(
            provider=provider,
            context=provider_context,
            remember_authorization=policy(ProviderMutation.REMEMBER, provider_context),
            export_authorization=policy(ProviderMutation.EXPORT, provider_context),
        )


def _fixture_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(FIXTURES, root)
    return root.resolve()


def _rebuilder(
    root: Path,
    *,
    relations: tuple[RelationRecord, ...] = (),
) -> tuple[GenerationRebuilder, InMemoryStageFactory]:
    project_id = "fixture-alpha"
    dataset_id = "fixture-alpha-memory"
    registry = RegistryBundle(
        sources=load_source_registry(root / "source_registry.csv"),
        profiles=(),
        relations=(),
    )
    factory = InMemoryStageFactory(project_id=project_id, dataset_id=dataset_id)
    service = GenerationRebuilder(
        boundary=ProjectBoundary(project_id=project_id, dataset_id=dataset_id, root=root),
        registry=registry,
        derived_root=".sys4ai/memory",
        profile_versions={"base@1": "1.0.0"},
        profile_registry_sha256=PROFILE_SHA,
        schema_paths=("schemas/relay.schema.json",),
        configuration_sha256=CONFIG_SHA,
        adapter_versions={name: "1.0.0" for name in available_adapters()},
        provider_name="in_memory",
        provider_version=IN_MEMORY_PROVIDER_VERSION,
        model_identifiers=("deterministic-no-model",),
        provider_factory=factory,
        relations=relations,
    )
    return service, factory


def _initialize_fixture_project(root: Path) -> Path:
    # This copied ingestion fixture contains an illustrative config. Prepare a
    # complete, project-bound consumer contract before exercising real bootstrap;
    # product registry rows alone omit their required schemas and profiles.
    configuration_path = root / "config/memory.toml"
    configuration_path.unlink()
    prepare_project_memory(root, "fixture-alpha", "Fixture Alpha", "fixture-director")
    loaded = load_configuration(configuration_path, trusted_project_root=root)
    preview = build_initialization_preview(
        loaded,
        included_source_count=11,
        excluded_source_count=0,
    )
    return apply_initialization(
        loaded,
        preview,
        accepted_impact_digest=preview.impact_digest,
        authorized=True,
    )


def _fixture_relation(root: Path) -> RelationRecord:
    registry = load_source_registry(root / "source_registry.csv")
    report = SourceDiscovery(
        project_root=root,
        project_id="fixture-alpha",
        entries=registry,
    ).discover()
    synchronized = IngestionSynchronizer(project_root=root).synchronize(report, force=True)
    assert not synchronized.failures
    records = sorted(
        (
            record
            for document in synchronized.documents
            for record in document.records
        ),
        key=lambda record: record.record_id,
    )
    assert len(records) >= 2
    relation = retrieval_relation_record(
        "rel_REBUILD_RESTORES",
        records[0].record_id,
        records[1].record_id,
        state="verified",
        confidence=1.0,
    ).to_json_dict()
    relation.update(
        {
            "project_id": "fixture-alpha",
            "source": {
                "source_id": records[0].source.source_id,
                "locator": dict(records[0].source.locator),
            },
        }
    )
    return RelationRecord.model_validate(relation)


def _generation_snapshot(root: Path, generation_id: str) -> ProviderSnapshot:
    path = root / ".sys4ai/memory/generations" / generation_id / "provider-snapshot.json"
    return ProviderSnapshot.model_validate_json(path.read_text(encoding="utf-8"))


def _authorization(preview_digest: str) -> AuthorizedRebuildImpact:
    return AuthorizedRebuildImpact(
        decision=AuthorizationDecision(
            allowed=True,
            reason_code="allowed",
            principal_id="admin_fixture",
            project_id="fixture-alpha",
            dataset_id="fixture-alpha-memory",
            operation="memory.rebuild.activate",
            permission=Permission.REBUILD,
            permission_revision="revision-1",
            canonical_sha256="a" * 64,
            grant_id="grant-rebuild",
        ),
        impact_digest=preview_digest,
    )


@pytest.mark.asyncio
async def test_clean_full_rebuild_restores_exact_and_provider_generations(
    tmp_path: Path,
) -> None:
    root = _fixture_root(tmp_path)
    initialization_receipt = _initialize_fixture_project(root)
    assert initialization_receipt.is_file()
    assert (root / ".sys4ai/memory").is_dir()
    relation = _fixture_relation(root)
    canonical_before = _canonical_snapshot(root)
    service, factory = _rebuilder(root, relations=(relation,))
    preview = service.preview(operation_id="clean-rebuild-1", mode=RebuildMode.FULL)

    assert preview.fingerprints.source_registry_sha256
    assert preview.fingerprints.profile_registry_sha256 == PROFILE_SHA
    assert preview.fingerprints.schema_set_sha256
    assert preview.fingerprints.configuration_sha256 == CONFIG_SHA
    assert preview.impact.source_revisions
    receipt = await service.execute(
        preview,
        authorization=_authorization(preview.impact_digest),
    )

    assert receipt.outcome is RebuildOutcome.SUCCEEDED
    assert receipt.activated
    assert receipt.prior_generation_preserved
    assert receipt.receipt.source_revisions
    assert receipt.receipt.configuration_fingerprint == CONFIG_SHA
    assert receipt.receipt.profile_versions == {"base@1": "1.0.0"}
    assert receipt.receipt.adapter_versions
    assert receipt.receipt.provider_version == IN_MEMORY_PROVIDER_VERSION
    assert receipt.receipt.model_identifiers == ("deterministic-no-model",)
    assert factory.providers[receipt.generation_id]
    initial_snapshot = _generation_snapshot(root, receipt.generation_id)
    initial_record_ids = {record.record_id for record in initial_snapshot.records}
    initial_source_ids = {source.source_id for source in initial_snapshot.sources}
    assert {item.relation_id for item in initial_snapshot.relations} == {
        "rel_REBUILD_RESTORES"
    }
    assert {
        relation.source_record_id,
        relation.target_record_id,
    } <= initial_record_ids
    assert all(record.source.source_id in initial_source_ids for record in initial_snapshot.records)
    pointer = json.loads(
        (root / ".sys4ai/memory/active-generation.json").read_text(encoding="utf-8")
    )
    assert pointer["generation_id"] == receipt.generation_id
    exact_path = root / ".sys4ai/memory/generations" / receipt.generation_id / "exact-index.sqlite3"
    with ExactIndex(exact_path) as index:
        exact = index.query_exact(project_id="fixture-alpha", query="REQ-ALPHA-042")
        assert exact
        assert exact[0].source.source_id in initial_source_ids
        assert index.health("fixture-alpha").current_source_count == receipt.source_count
    assert not service.drift().drifted
    assert _canonical_snapshot(root) == canonical_before

    first_revisions = tuple(
        (item.source_id, item.content_sha256) for item in receipt.receipt.source_revisions
    )
    shutil.rmtree(root / ".sys4ai/memory")
    assert not (root / ".sys4ai/memory").exists()
    rebuilt_relation = _fixture_relation(root)
    assert rebuilt_relation == relation
    replacement, _ = _rebuilder(root, relations=(rebuilt_relation,))
    replacement_preview = replacement.preview(operation_id="clean-rebuild-2", mode=RebuildMode.FULL)
    replacement_receipt = await replacement.execute(
        replacement_preview,
        authorization=_authorization(replacement_preview.impact_digest),
    )
    assert replacement_receipt.outcome is RebuildOutcome.SUCCEEDED
    assert (
        tuple(
            (item.source_id, item.content_sha256)
            for item in replacement_receipt.receipt.source_revisions
        )
        == first_revisions
    )
    rebuilt_exact = (
        root
        / ".sys4ai/memory/generations"
        / replacement_receipt.generation_id
        / "exact-index.sqlite3"
    )
    rebuilt_snapshot = _generation_snapshot(root, replacement_receipt.generation_id)
    assert {record.record_id for record in rebuilt_snapshot.records} == initial_record_ids
    assert {source.source_id for source in rebuilt_snapshot.sources} == initial_source_ids
    assert {item.relation_id for item in rebuilt_snapshot.relations} == {
        "rel_REBUILD_RESTORES"
    }
    with ExactIndex(rebuilt_exact) as index:
        exact = index.query_exact(project_id="fixture-alpha", query="REQ-ALPHA-042")
        assert exact
        assert exact[0].source.source_id in initial_source_ids
    assert _canonical_snapshot(root) == canonical_before


@pytest.mark.asyncio
async def test_failed_generation_keeps_prior_pointer_and_reports_checkpoint(
    tmp_path: Path,
) -> None:
    root = _fixture_root(tmp_path)
    service, _ = _rebuilder(root)
    initial_preview = service.preview(operation_id="initial", mode=RebuildMode.FULL)
    initial = await service.execute(
        initial_preview,
        authorization=_authorization(initial_preview.impact_digest),
    )
    pointer_path = root / ".sys4ai/memory/active-generation.json"
    pointer_before = pointer_path.read_bytes()

    failed_preview = service.preview(operation_id="failed", mode=RebuildMode.FULL)

    def fail_before_activation(stage: RebuildStage) -> None:
        if stage is RebuildStage.VALIDATION:
            raise RuntimeError("fixture fault")

    failed = await service.execute(
        failed_preview,
        authorization=_authorization(failed_preview.impact_digest),
        fault_hook=fail_before_activation,
    )

    assert failed.outcome is RebuildOutcome.FAILED
    assert not failed.activated
    assert failed.prior_generation_preserved
    assert failed.failure_code == "RuntimeError"
    assert failed.checkpoint.stage is RebuildStage.VALIDATION
    assert pointer_path.read_bytes() == pointer_before
    assert json.loads(pointer_before)["generation_id"] == initial.generation_id
    with ExactIndex(
        root / ".sys4ai/memory/generations" / initial.generation_id / "exact-index.sqlite3"
    ) as index:
        assert index.query_exact(project_id="fixture-alpha", query="REQ-ALPHA-042")


@pytest.mark.asyncio
async def test_cancellation_and_incremental_drift_are_observable(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    service, _ = _rebuilder(root)
    initial_preview = service.preview(operation_id="initial", mode=RebuildMode.FULL)
    initial = await service.execute(
        initial_preview,
        authorization=_authorization(initial_preview.impact_digest),
    )
    pointer_path = root / ".sys4ai/memory/active-generation.json"
    pointer_before = pointer_path.read_bytes()
    notes = root / "notes/operator.txt"
    notes.write_text(notes.read_text(encoding="utf-8") + "changed drift token\n", encoding="utf-8")
    drift = service.drift()
    assert drift.drifted
    assert any(item.identity == "src_alpha-notes" for item in drift.items)

    incremental_preview = service.preview(
        operation_id="incremental-cancel", mode=RebuildMode.INCREMENTAL
    )
    assert incremental_preview.impact.delta.changed == 1
    observed: list[RebuildStage] = []
    cancelled = await service.execute(
        incremental_preview,
        authorization=_authorization(incremental_preview.impact_digest),
        progress_callback=lambda event: observed.append(event.stage),
        cancel_requested=lambda stage: stage is RebuildStage.EXACT_INDEX,
    )

    assert cancelled.outcome is RebuildOutcome.CANCELLED
    assert cancelled.checkpoint.cancel_requested
    assert RebuildStage.DISCOVERY in observed
    assert RebuildStage.NORMALIZATION in observed
    assert RebuildStage.EXACT_INDEX in observed
    assert pointer_path.read_bytes() == pointer_before
    assert json.loads(pointer_before)["generation_id"] == initial.generation_id


@pytest.mark.asyncio
async def test_incremental_generation_reconciles_add_change_move_and_delete(
    tmp_path: Path,
) -> None:
    root = _fixture_root(tmp_path)
    service, _ = _rebuilder(root)
    initial_preview = service.preview(operation_id="initial", mode=RebuildMode.FULL)
    initial = await service.execute(
        initial_preview,
        authorization=_authorization(initial_preview.impact_digest),
    )
    assert initial.outcome is RebuildOutcome.SUCCEEDED

    registry_path = root / "source_registry.csv"
    lines = registry_path.read_text(encoding="utf-8").splitlines()
    rewritten: list[str] = []
    for line in lines:
        if line.startswith("src_alpha-events,"):
            continue
        if line.startswith("src_alpha-notes,"):
            line = line.replace("notes/operator.txt", "notes/moved.txt")
        rewritten.append(line)
    rewritten.append(
        "src_alpha-added,fixture-alpha,notes/added.txt,text,canonical,A3,"
        "project-authored,internal,project/fixture-alpha,text,true"
    )
    registry_path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
    (root / "notes/operator.txt").rename(root / "notes/moved.txt")
    (root / "notes/added.txt").write_text(
        "Literal phrase: newly indexed incremental source.\n", encoding="utf-8"
    )
    requirements = root / "docs/requirements.md"
    requirements.write_text(
        requirements.read_text(encoding="utf-8") + "\nIncremental change marker.\n",
        encoding="utf-8",
    )
    (root / "events/history.jsonl").unlink()

    incremental, _ = _rebuilder(root)
    preview = incremental.preview(operation_id="all-delta-kinds", mode=RebuildMode.INCREMENTAL)
    assert preview.impact.delta.added == 1
    assert preview.impact.delta.moved == 1
    assert preview.impact.delta.deleted == 1
    assert preview.impact.delta.changed >= 2
    receipt = await incremental.execute(
        preview,
        authorization=_authorization(preview.impact_digest),
    )
    assert receipt.outcome is RebuildOutcome.SUCCEEDED
    exact_path = root / ".sys4ai/memory/generations" / receipt.generation_id / "exact-index.sqlite3"
    with ExactIndex(exact_path) as index:
        assert index.query_exact(
            project_id="fixture-alpha", query="newly indexed incremental source"
        )
        moved = index.query_exact(project_id="fixture-alpha", query="notes/moved.txt", field="path")
        assert moved
        assert not index.query_exact(
            project_id="fixture-alpha", query="notes/operator.txt", field="path"
        )


def test_preview_and_drift_without_generation_do_not_create_derived_state(
    tmp_path: Path,
) -> None:
    root = _fixture_root(tmp_path)
    service, _ = _rebuilder(root)

    drift = service.drift()
    preview = service.preview(operation_id="read-only", mode=RebuildMode.FULL)

    assert drift.drifted
    assert drift.active_generation_id is None
    assert preview.impact.previous_generation_id is None
    assert not (root / ".sys4ai").exists()


@pytest.mark.asyncio
async def test_stale_preview_is_rejected_before_derived_state_is_created(
    tmp_path: Path,
) -> None:
    root = _fixture_root(tmp_path)
    service, _ = _rebuilder(root)
    preview = service.preview(operation_id="stale", mode=RebuildMode.FULL)
    notes = root / "notes/operator.txt"
    notes.write_text(notes.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")

    with pytest.raises(RebuildConflictError, match="changed after preview"):
        await service.execute(
            preview,
            authorization=_authorization(preview.impact_digest),
        )
    assert not (root / ".sys4ai").exists()


@pytest.mark.asyncio
async def test_rebuild_authorization_must_match_exact_preview(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    service, _ = _rebuilder(root)
    preview = service.preview(operation_id="authorization", mode=RebuildMode.FULL)

    with pytest.raises(RebuildAuthorizationError, match="does not match preview"):
        await service.execute(
            preview,
            authorization=_authorization("b" * 64),
        )
    assert not (root / ".sys4ai").exists()


def test_tampered_active_pointer_is_rejected_without_path_traversal(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    service, _ = _rebuilder(root)
    pointer = root / ".sys4ai/memory/active-generation.json"
    pointer.parent.mkdir(parents=True)
    pointer.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "project_id": "fixture-alpha",
                "dataset_id": "fixture-alpha-memory",
                "generation_id": "gen_../../outside",
                "manifest_sha256": "a" * 64,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RebuildError, match="invalid generation ID"):
        service.drift()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filename", "identity"),
    (
        ("exact-index.sqlite3", "exact_index"),
        ("provider-snapshot.json", "provider_snapshot"),
    ),
)
async def test_drift_detects_generated_artifact_hand_edits(
    tmp_path: Path,
    filename: str,
    identity: str,
) -> None:
    root = _fixture_root(tmp_path)
    service, _ = _rebuilder(root)
    preview = service.preview(operation_id=f"tamper-{identity}", mode=RebuildMode.FULL)
    receipt = await service.execute(
        preview,
        authorization=_authorization(preview.impact_digest),
    )
    artifact = root / ".sys4ai/memory/generations" / receipt.generation_id / filename
    artifact.write_bytes(artifact.read_bytes() + b"fixture-hand-edit")

    drift = service.drift()

    assert drift.drifted
    assert any(
        item.kind.value == "generation"
        and item.identity == f"{receipt.generation_id}/{identity}"
        and item.expected != item.observed
        for item in drift.items
    )
