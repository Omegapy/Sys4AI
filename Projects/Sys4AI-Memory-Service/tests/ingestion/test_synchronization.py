from __future__ import annotations

from pathlib import Path

from sys4ai_memory.exact_index import ExactIndex
from sys4ai_memory.ingestion import (
    IngestionSynchronizer,
    SourceChangeKind,
    SourceManifest,
    SourceManifestEntry,
    compare_manifests,
    load_manifest,
)
from sys4ai_memory.sources import SourceDiscovery, load_source_registry

PROJECT_ROOT = Path(__file__).parents[2]
LIFECYCLE_ROOT = PROJECT_ROOT / "tests/fixtures/lifecycle"


def test_lifecycle_fixture_classifies_unchanged_added_changed_moved_and_deleted() -> None:
    before = load_manifest(LIFECYCLE_ROOT / "source_manifest_before.json")
    after = load_manifest(LIFECYCLE_ROOT / "source_manifest_after.json")
    delta = compare_manifests(before, after)

    observed = {change.source_id: change.change for change in delta.changes}
    assert observed == {
        "src_lifecycle-move": SourceChangeKind.MOVED,
        "src_lifecycle-change": SourceChangeKind.CHANGED,
        "src_lifecycle-delete": SourceChangeKind.DELETED,
        "src_lifecycle-add": SourceChangeKind.ADDED,
    }


def test_manifest_recovers_unique_hash_moves_and_marks_resume() -> None:
    digest = "a" * 64
    before = SourceManifest(
        "fixture",
        (SourceManifestEntry("src_old", "docs/old.md", digest),),
    )
    moved = SourceManifest(
        "fixture",
        (SourceManifestEntry("src_new", "docs/new.md", digest),),
    )
    moved_delta = compare_manifests(before, moved)

    assert len(moved_delta.changes) == 1
    assert moved_delta.changes[0].change is SourceChangeKind.MOVED
    assert moved_delta.changes[0].source_id == "src_old"
    assert moved_delta.changes[0].matched_by == "unique_content_sha256"

    failed = SourceManifest(
        "fixture",
        (SourceManifestEntry("src_old", "docs/old.md", digest, status="failed"),),
    )
    resumed = compare_manifests(failed, before)
    assert resumed.changes[0].change is SourceChangeKind.RESUMED


def _write_registry(root: Path) -> Path:
    registry = root / "source_registry.csv"
    registry.write_text(
        "source_id,project_id,path,format,canonicality,authority_tier,trust_class,"
        "sensitivity,namespace,adapter,include_flag\n"
        "src_sync-good,fixture-sync,good.txt,text,canonical,A3,project-authored,"
        "internal,project/fixture-sync,text,true\n"
        "src_sync-json,fixture-sync,bad.json,json,canonical,A3,project-authored,"
        "internal,project/fixture-sync,json,true\n",
        encoding="utf-8",
    )
    return registry


def _discover(root: Path, registry: Path):
    return SourceDiscovery(
        project_root=root,
        project_id="fixture-sync",
        entries=load_source_registry(registry),
    ).discover()


def test_incremental_sync_preserves_valid_index_on_failure_then_resumes(tmp_path: Path) -> None:
    root = (tmp_path / "project").resolve()
    root.mkdir()
    registry = _write_registry(root)
    (root / "good.txt").write_text("first stable phrase\n", encoding="utf-8")
    (root / "bad.json").write_text('{"id":"OLD-ID"}\n', encoding="utf-8")

    with ExactIndex(":memory:") as index:
        synchronizer = IngestionSynchronizer(project_root=root, index_writer=index)
        initial = synchronizer.synchronize(_discover(root, registry))
        assert not initial.failures
        assert {item.change for item in initial.delta.changes} == {SourceChangeKind.ADDED}
        assert index.query_exact(project_id="fixture-sync", query="OLD-ID")

        (root / "good.txt").write_text("replacement stable phrase\n", encoding="utf-8")
        (root / "bad.json").write_text('{"id":', encoding="utf-8")
        partial = synchronizer.synchronize(
            _discover(root, registry),
            previous_manifest=initial.manifest,
            checkpoint=initial.checkpoint,
        )

        assert len(partial.failures) == 1
        assert partial.failures[0].source_id == "src_sync-json"
        assert index.query_exact(project_id="fixture-sync", query="OLD-ID")
        assert index.query_lexical(
            project_id="fixture-sync", query="replacement stable phrase", phrase=True
        )
        revised_good = index.current_source_records(
            project_id="fixture-sync", source_id="src_sync-good"
        )
        assert revised_good
        assert {record.version for record in revised_good} == {2}
        assert {record.created_at for record in revised_good} == {
            record.created_at
            for record in initial.documents[0].records
        }

        (root / "bad.json").write_text('{"id":"NEW-ID"}\n', encoding="utf-8")
        resumed = synchronizer.synchronize(
            _discover(root, registry),
            previous_manifest=partial.manifest,
            checkpoint=partial.checkpoint,
        )

        assert not resumed.failures
        assert any(
            item.source_id == "src_sync-json" and item.change is SourceChangeKind.RESUMED
            for item in resumed.delta.changes
        )
        assert index.query_exact(project_id="fixture-sync", query="NEW-ID")
        assert not index.query_exact(project_id="fixture-sync", query="OLD-ID")
        assert index.query_exact(
            project_id="fixture-sync", query="OLD-ID", current_only=False
        )

        forced = synchronizer.synchronize(
            _discover(root, registry),
            previous_manifest=resumed.manifest,
            checkpoint=resumed.checkpoint,
            force=True,
        )
        assert not forced.failures
        assert {
            record.record_id: record.version
            for record in index.current_source_records(
                project_id="fixture-sync", source_id="src_sync-json"
            )
        } == {
            record.record_id: record.version
            for record in resumed.documents[0].records
        }

        (root / "good.txt").unlink()
        deleted = synchronizer.synchronize(
            _discover(root, registry),
            previous_manifest=resumed.manifest,
            checkpoint=resumed.checkpoint,
        )
        assert any(
            item.source_id == "src_sync-good" and item.change is SourceChangeKind.DELETED
            for item in deleted.delta.changes
        )
        assert not index.query_lexical(
            project_id="fixture-sync", query="replacement stable phrase", phrase=True
        )
        assert index.query_lexical(
            project_id="fixture-sync",
            query="replacement stable phrase",
            phrase=True,
            current_only=False,
        )
