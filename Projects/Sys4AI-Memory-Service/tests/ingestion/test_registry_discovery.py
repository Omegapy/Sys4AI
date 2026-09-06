from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sys4ai_memory.contracts import AuthorityTier, Sensitivity, TrustClass
from sys4ai_memory.sources import (
    DiscoveryDisposition,
    DiscoveryReason,
    RegistryValidationError,
    SourceDiscovery,
    SourceRegistryEntry,
    load_registry_bundle,
    load_source_registry,
)

PROJECT_ROOT = Path(__file__).parents[2]
FIXTURE_ROOT = PROJECT_ROOT / "tests/fixtures/projects/project_alpha"


def _entry(
    *,
    source_id: str,
    path: str | None = None,
    pattern: str | None = None,
    include: bool = True,
    source_kind: str | None = None,
    format_name: str = "text",
) -> SourceRegistryEntry:
    return SourceRegistryEntry(
        source_id=source_id,
        project_id="fixture-security",
        path_or_uri=path,
        path_pattern=pattern,
        source_kind=source_kind or ("path_rule" if pattern else "file"),
        format=format_name,
        canonicality="canonical" if include else "excluded",
        content_role="test-source" if include else "excluded-path",
        authority_tier=AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE,
        trust_class=TrustClass.PROJECT_AUTHORED if include else TrustClass.UNTRUSTED,
        sensitivity=Sensitivity.INTERNAL if include else Sensitivity.SECRET_PROHIBITED,
        namespace="project/fixture-security" if include else "excluded",
        profile_id="base@1",
        ingestion_adapter=format_name if include else "none",
        chunking_profile="paragraph@1" if include else "none",
        schema_ref=None,
        refresh_mode="git-revision" if include else "static",
        retention_policy="canonical" if include else "none",
        owner="fixture-security",
        write_policy="deny",
        include_flag=include,
        notes="Synthetic test registration",
    )


def test_loads_full_registry_bundle_and_compact_fixture_registry() -> None:
    bundle = load_registry_bundle(
        source_registry=PROJECT_ROOT / "registries/memory_source_registry.csv",
        profile_registry=PROJECT_ROOT / "registries/memory_profile_registry.csv",
        relation_registry=PROJECT_ROOT / "registries/memory_relation_registry.csv",
        project_root=PROJECT_ROOT,
    )
    fixture = load_source_registry(FIXTURE_ROOT / "source_registry.csv")

    assert len(bundle.profiles) == 2
    assert len(bundle.relations) == 32
    assert {item.source_id for item in fixture} >= {
        "src_alpha-requirements",
        "src_alpha-code",
    }
    assert {item.source_id for item in bundle.sources} >= {
        "src_MEM-OPS-001",
        "src_MEM-PERMISSIONS-001",
        "src_MEM-PROFILE-SE-001",
        "src_EXCLUDE-MODELS-001",
    }
    assert all(item.profile_id == "base@1" for item in fixture)


def test_root_folder_rules_do_not_match_nested_folders_with_the_same_name(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    for name in ("tests/root.txt", "SKILLS-depo/tool/tests/skill.txt", "Other/tests/new.txt"):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("independent canonical source\n")
    discovery = SourceDiscovery(
        project_root=root,
        project_id="fixture-security",
        entries=(
            _entry(source_id="src_root_tests", pattern="tests/**/*.txt"),
            _entry(source_id="src_skill_source", pattern="SKILLS-depo/**/*.txt"),
        ),
    )
    report = discovery.discover(candidate_paths=("Other/tests/new.txt",))
    assert {record.path_or_uri for record in report.records} == {
        "tests/root.txt",
        "SKILLS-depo/tool/tests/skill.txt",
    }
    assert discovery.explain_path("Other/tests/new.txt").reason is DiscoveryReason.DEFAULT_DENY
    assert all(item.reason is not DiscoveryReason.AMBIGUOUS for item in report.decisions)
    source_rules = {
        record.path_or_uri: record.locator["registry_rule_id"] for record in report.records
    }
    assert source_rules["tests/root.txt"] == "src_root_tests"
    assert source_rules["SKILLS-depo/tool/tests/skill.txt"] == "src_skill_source"


def test_single_star_is_one_segment_and_leading_double_star_excludes_at_any_depth(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    for name in ("docs/root.txt", "docs/sub/nested.txt", "logs/root.txt", "docs/logs/nested.txt"):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("bounded source\n")
    discovery = SourceDiscovery(
        project_root=root,
        project_id="fixture-security",
        entries=(
            _entry(source_id="src_docs", pattern="docs/*.txt"),
            _entry(source_id="src_logs", pattern="**/logs/**", include=False),
        ),
    )
    assert discovery.explain_path("docs/root.txt").disposition is DiscoveryDisposition.INCLUDED
    assert discovery.explain_path("docs/sub/nested.txt").reason is DiscoveryReason.DEFAULT_DENY
    for name in ("logs/root.txt", "docs/logs/nested.txt"):
        assert discovery.explain_path(name).reason is DiscoveryReason.REGISTERED_EXCLUSION


def test_product_registry_includes_operations_and_excludes_downloaded_models() -> None:
    bundle = load_registry_bundle(
        source_registry=PROJECT_ROOT / "registries/memory_source_registry.csv",
        profile_registry=PROJECT_ROOT / "registries/memory_profile_registry.csv",
        relation_registry=PROJECT_ROOT / "registries/memory_relation_registry.csv",
        project_root=PROJECT_ROOT,
    )
    discovery = SourceDiscovery(
        project_root=PROJECT_ROOT,
        project_id="sys4ai-memory-service",
        entries=bundle.sources,
    )

    operations = discovery.explain_path("docs/operations/README.md")
    model = discovery.explain_path("models/ollama/blobs/example-model-blob")

    assert operations.disposition is DiscoveryDisposition.INCLUDED
    assert operations.rule_ids == ("src_MEM-OPS-001",)
    assert model.disposition is DiscoveryDisposition.EXCLUDED
    assert model.reason is DiscoveryReason.REGISTERED_EXCLUSION
    assert model.rule_ids == ("src_EXCLUDE-MODELS-001",)


@pytest.mark.parametrize(
    ("replacement", "expected"),
    [
        ("A3", "A9"),
        ("fixture-alpha", " fixture-alpha"),
    ],
)
def test_registry_rejects_unsupported_enums_and_outer_whitespace(
    tmp_path: Path, replacement: str, expected: str
) -> None:
    source = (FIXTURE_ROOT / "source_registry.csv").read_text(encoding="utf-8")
    candidate = tmp_path / "sources.csv"
    candidate.write_text(source.replace(replacement, expected, 1), encoding="utf-8")

    with pytest.raises(RegistryValidationError):
        load_source_registry(candidate)


def test_registry_rejects_duplicate_ids_and_unresolved_profiles(tmp_path: Path) -> None:
    lines = (FIXTURE_ROOT / "source_registry.csv").read_text(encoding="utf-8").splitlines()
    duplicate = tmp_path / "duplicate.csv"
    duplicate.write_text("\n".join((*lines, lines[1])) + "\n", encoding="utf-8")

    with pytest.raises(RegistryValidationError, match="duplicate source_id"):
        load_source_registry(duplicate)
    with pytest.raises(RegistryValidationError, match="unresolved profile_id"):
        load_source_registry(FIXTURE_ROOT / "source_registry.csv", known_profiles={"other@1"})


def test_one_time_registration_is_explicit_and_unique() -> None:
    bundle = load_registry_bundle(
        source_registry=PROJECT_ROOT / "registries/memory_source_registry.csv",
        profile_registry=PROJECT_ROOT / "registries/memory_profile_registry.csv",
        relation_registry=PROJECT_ROOT / "registries/memory_relation_registry.csv",
        project_root=PROJECT_ROOT,
    )
    template = next(item for item in bundle.sources if item.source_id == "src_MEM-PRD-001")
    one_time = replace(
        template,
        source_id="src_one-time-readme",
        path_or_uri="README.md",
        registry_path=None,
        row_number=None,
    )
    updated = bundle.with_one_time_sources((one_time,))

    assert updated.sources[-1].one_time is True
    with pytest.raises(RegistryValidationError, match="duplicate source_id"):
        updated.with_one_time_sources((one_time,))


def test_generated_registration_requires_canonical_input_and_lower_authority() -> None:
    bundle = load_registry_bundle(
        source_registry=PROJECT_ROOT / "registries/memory_source_registry.csv",
        profile_registry=PROJECT_ROOT / "registries/memory_profile_registry.csv",
        relation_registry=PROJECT_ROOT / "registries/memory_relation_registry.csv",
        project_root=PROJECT_ROOT,
    )
    template = next(item for item in bundle.sources if item.source_id == "src_MEM-PRD-001")
    generated = replace(
        template,
        source_id="src_generated-readme",
        path_or_uri="README.md",
        source_kind="generated",
        canonicality="generated",
        content_role="generated-document",
        authority_tier=AuthorityTier.AGENT_DURABLE_MATERIAL,
        trust_class=TrustClass.AGENT_GENERATED,
        generated_from=("src_MEM-PRD-001",),
        registry_path=None,
        row_number=None,
    )

    assert bundle.with_one_time_sources((generated,)).sources[-1].generated_from == (
        "src_MEM-PRD-001",
    )
    with pytest.raises(RegistryValidationError, match="unresolved generated_from"):
        bundle.with_one_time_sources(
            (replace(generated, source_id="src_generated-missing", generated_from=("src_nope",)),)
        )
    with pytest.raises(RegistryValidationError, match="cannot outrank"):
        bundle.with_one_time_sources(
            (
                replace(
                    generated,
                    source_id="src_generated-overreach",
                    authority_tier=AuthorityTier.SYSTEM_POLICY,
                ),
            )
        )


def test_discovery_fails_closed_before_reading_excluded_paths(tmp_path: Path) -> None:
    root = (tmp_path / "project").resolve()
    root.mkdir()
    (root / "good.txt").write_text("safe\n", encoding="utf-8")
    (root / "oversized.txt").write_text("x" * 101, encoding="utf-8")
    (root / "unknown.md").write_text("unregistered\n", encoding="utf-8")
    (root / "secret-content.txt").write_text("api_key=unit-test-marker", encoding="utf-8")
    (root / ".env").write_text("fixture marker", encoding="utf-8")
    (root / ".sys4ai/memory").mkdir(parents=True)
    (root / ".sys4ai/memory/cache.txt").write_text("derived\n", encoding="utf-8")
    (root / "blocked").mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (root / "blocked/source.txt").symlink_to(outside)
    (root / "link.txt").symlink_to(outside)
    fifo = root / "device.txt"
    os.mkfifo(fifo)

    ignored_created = False
    git = shutil.which("git")
    if git is not None:
        subprocess.run(  # noqa: S603 - fixed executable in disposable test root
            [git, "init", "-q", str(root)], check=True, capture_output=True
        )
        (root / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
        (root / "ignored.txt").write_text("ignored\n", encoding="utf-8")
        ignored_created = True

    entries = (
        _entry(source_id="src_include-text", pattern="**/*.txt"),
        _entry(
            source_id="src_exclude-blocked",
            pattern="blocked/**",
            include=False,
            source_kind="exclusion_rule",
            format_name="any",
        ),
    )
    report = SourceDiscovery(
        project_root=root,
        project_id="fixture-security",
        entries=entries,
        max_file_bytes=100,
    ).discover(candidate_paths=("unknown.md", ".env", "../escape.txt"))
    by_path = {item.path_or_uri: item for item in report.decisions}

    assert [item.path_or_uri for item in report.records] == ["good.txt"]
    assert by_path["blocked/source.txt"].reason is DiscoveryReason.REGISTERED_EXCLUSION
    assert by_path["link.txt"].reason is DiscoveryReason.SYMLINK
    assert by_path["device.txt"].reason is DiscoveryReason.NOT_REGULAR
    assert by_path["oversized.txt"].reason is DiscoveryReason.OVERSIZED
    assert by_path["secret-content.txt"].reason is DiscoveryReason.SECRET_CONTENT
    assert by_path[".env"].reason is DiscoveryReason.SECRET_PATH
    assert by_path[".sys4ai/memory/cache.txt"].reason is DiscoveryReason.GENERATED_PATH
    assert by_path["unknown.md"].reason is DiscoveryReason.DEFAULT_DENY
    assert by_path["../escape.txt"].reason is DiscoveryReason.UNSAFE_PATH
    if ignored_created:
        assert by_path["ignored.txt"].reason is DiscoveryReason.GIT_IGNORED
    assert all(
        item.disposition is not DiscoveryDisposition.INCLUDED
        for path, item in by_path.items()
        if path != "good.txt"
    )


def test_exclusion_precedes_ambiguous_includes_and_explain_does_not_read(tmp_path: Path) -> None:
    root = (tmp_path / "project").resolve()
    root.mkdir()
    outside = tmp_path / "blocked-outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (root / "blocked.txt").symlink_to(outside)
    (root / "ambiguous.txt").write_text("safe\n", encoding="utf-8")
    entries = (
        _entry(source_id="src_include-all", pattern="*.txt"),
        _entry(source_id="src_include-exact", path="ambiguous.txt"),
        _entry(
            source_id="src_block",
            path="blocked.txt",
            include=False,
            source_kind="exclusion_rule",
            format_name="any",
        ),
    )
    discovery = SourceDiscovery(project_root=root, project_id="fixture-security", entries=entries)

    assert discovery.explain_path("blocked.txt").reason is DiscoveryReason.REGISTERED_EXCLUSION
    assert discovery.explain_path("ambiguous.txt").reason is DiscoveryReason.AMBIGUOUS


def test_explicit_external_registration_preserves_origin_metadata() -> None:
    entry = replace(
        _entry(source_id="src_external-evidence", path="note.txt"),
        path_or_uri="https://example.invalid/evidence/1",
        source_kind="external",
        canonicality="evidential",
        content_role="external-evidence",
        authority_tier=AuthorityTier.EXTERNAL_EVIDENCE,
        trust_class=TrustClass.EXTERNAL_UNVERIFIED,
        ingestion_adapter="text",
        one_time=True,
    )
    discovery = SourceDiscovery(
        project_root=PROJECT_ROOT,
        project_id="fixture-security",
        entries=(entry,),
    )
    retrieved = datetime(2026, 9, 3, tzinfo=UTC)
    record = discovery.discover_external(
        entry,
        content=b"External evidence fixture.\n",
        retrieved_at=retrieved,
        licensing_metadata={"license": "test-only"},
        access_metadata={"access": "public-fixture"},
    )

    assert record.origin_uri == "https://example.invalid/evidence/1"
    assert record.retrieved_at == retrieved
    assert record.licensing_metadata == {"license": "test-only"}
    assert record.access_metadata == {"access": "public-fixture"}
    assert record.locator["one_time_registration"] is True


def test_git_root_discovery_records_commit_blob_and_dirty_revision(tmp_path: Path) -> None:
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is unavailable")
    root = (tmp_path / "git-project").resolve()
    root.mkdir()
    source_path = root / "tracked.md"
    source_path.write_text("# Tracked\n\nInitial source.\n", encoding="utf-8")
    commands = (
        ("init", "-q"),
        ("add", "tracked.md"),
        (
            "-c",
            "user.name=Sys4AI Test",
            "-c",
            "user.email=sys4ai-test@example.invalid",
            "commit",
            "-q",
            "-m",
            "fixture",
        ),
    )
    for arguments in commands:
        subprocess.run(  # noqa: S603 - fixed executable and disposable test root
            [git, "-C", str(root), *arguments],
            check=True,
            capture_output=True,
        )
    entry = _entry(
        source_id="src_git-tracked",
        path="tracked.md",
        source_kind="file",
        format_name="markdown",
    )
    discovery = SourceDiscovery(
        project_root=root,
        project_id="fixture-security",
        entries=(entry,),
    )

    clean = discovery.discover().records[0]
    source_path.write_text("# Tracked\n\nChanged source.\n", encoding="utf-8")
    dirty = discovery.discover().records[0]

    assert clean.git_commit is not None
    assert clean.git_blob_sha is not None
    assert clean.working_tree_state == "clean"
    assert dirty.git_commit == clean.git_commit
    assert dirty.git_blob_sha == clean.git_blob_sha
    assert dirty.working_tree_state is not None
    assert dirty.working_tree_state.startswith("working-tree:")
    assert dirty.content_sha256 != clean.content_sha256
