from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from sys4ai_memory.contracts import Sensitivity, TrustClass
from sys4ai_memory.exchange import (
    ExchangePolicyError,
    ExportPolicy,
    ImportPolicy,
    MemoryPackageExporter,
    MemoryPackageValidator,
    MigrationPlanningError,
    MigrationRegistry,
    MigrationStep,
    PackageContainer,
    PackageValidationError,
)

from .test_memory_package import _export, _import_policy


def test_policy_models_reject_secret_and_unresolved_contradictions() -> None:
    with pytest.raises(ValidationError, match="secret-prohibited"):
        ExportPolicy(
            format_decision_status="pending-user-decision",
            allowed_sensitivities=frozenset({Sensitivity.SECRET_PROHIBITED}),
        )
    with pytest.raises(ValidationError, match="pending format policy"):
        ExportPolicy(
            format_decision_status="pending-user-decision",
            approved_encryption="age-x25519",
        )
    with pytest.raises(ValidationError, match="secret-prohibited"):
        ImportPolicy(
            target_project_id="project-alpha",
            target_dataset_id="project-alpha-memory",
            expected_profile_versions={"base@1": "1.0.0"},
            allowed_trust_classes=frozenset({TrustClass.HUMAN_APPROVED}),
            allowed_sensitivities=frozenset({Sensitivity.SECRET_PROHIBITED}),
        )
    with pytest.raises(ValidationError, match="explicit trust"):
        ImportPolicy(
            target_project_id="project-alpha",
            target_dataset_id="project-alpha-memory",
            expected_profile_versions={"base@1": "1.0.0"},
            allowed_trust_classes=frozenset(),
            allowed_sensitivities=frozenset({Sensitivity.INTERNAL}),
        )


def test_exporter_rejects_non_disposable_destinations_and_production_claims(
    tmp_path: Path,
) -> None:
    export_root = (tmp_path / "exports").resolve()
    export_root.mkdir()
    exporter = MemoryPackageExporter(disposable_root=export_root)
    from .test_memory_package import _snapshot

    with pytest.raises(ExchangePolicyError, match="configured export root"):
        exporter.export_snapshot(
            _snapshot(),
            destination=tmp_path / "outside",
            container=PackageContainer.DIRECTORY,
            policy=ExportPolicy(
                format_decision_status="pending-user-decision",
                allow_unencrypted_disposable_test_only=True,
            ),
            disposable_test_only=True,
        )
    with pytest.raises(ExchangePolicyError, match="new child path"):
        exporter.export_snapshot(
            _snapshot(),
            destination=export_root,
            container=PackageContainer.DIRECTORY,
            policy=ExportPolicy(
                format_decision_status="pending-user-decision",
                allow_unencrypted_disposable_test_only=True,
            ),
            disposable_test_only=True,
        )
    with pytest.raises(ExchangePolicyError, match="ZIP container"):
        exporter.export_snapshot(
            _snapshot(),
            destination=export_root / "production",
            container=PackageContainer.DIRECTORY,
            policy=ExportPolicy(
                format_decision_status="approved",
                approved_encryption="age-x25519",
            ),
        )


def test_directory_validation_fails_closed_for_structure_json_and_limits(
    tmp_path: Path,
) -> None:
    package = _export(tmp_path, name="source-package")
    with pytest.raises(ExchangePolicyError, match="unencrypted candidate import"):
        MemoryPackageValidator(
            _import_policy().model_copy(update={"allow_unencrypted_disposable_test_only": False})
        ).validate(package)

    missing = tmp_path / "missing-member"
    shutil.copytree(package, missing)
    (missing / "status.json").unlink()
    with pytest.raises(PackageValidationError, match="closed manifest"):
        MemoryPackageValidator(_import_policy()).validate(missing)

    duplicate_key = tmp_path / "duplicate-json-key"
    shutil.copytree(package, duplicate_key)
    (duplicate_key / "manifest.json").write_text(
        '{"schema_version":"1.0","schema_version":"1.0"}', encoding="utf-8"
    )
    with pytest.raises(PackageValidationError, match="manifest is absent or invalid"):
        MemoryPackageValidator(_import_policy()).validate(duplicate_key)

    symlink_package = tmp_path / "symlink-package"
    symlink_package.mkdir()
    (symlink_package / "manifest.json").symlink_to(package / "manifest.json")
    with pytest.raises(PackageValidationError, match="unsafe member"):
        MemoryPackageValidator(_import_policy()).validate(symlink_package)

    with pytest.raises(PackageValidationError, match="member count"):
        MemoryPackageValidator(_import_policy().model_copy(update={"max_members": 1})).validate(
            package
        )
    with pytest.raises(PackageValidationError, match="member exceeds"):
        MemoryPackageValidator(
            _import_policy().model_copy(update={"max_member_bytes": 10})
        ).validate(package)


def test_zip_rejects_unapproved_compression_method(tmp_path: Path) -> None:
    package = tmp_path / "bzip2.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_BZIP2) as archive:
        archive.writestr("manifest.json", "{}")
    with pytest.raises(PackageValidationError, match="compression method"):
        MemoryPackageValidator(_import_policy()).validate(package)


def test_migration_registry_validates_graph_and_identity_dry_run(tmp_path: Path) -> None:
    package = _export(tmp_path, name="migration-boundaries")
    validated = MemoryPackageValidator(_import_policy()).validate(package)
    first = MigrationStep(
        step_id="step-1",
        source_version="1.0.0",
        target_version="1.1.0",
        description="first transform",
    )
    second = MigrationStep(
        step_id="step-2",
        source_version="1.1.0",
        target_version="2.0.0",
        description="second transform",
    )
    registry = MigrationRegistry((first, second))
    identity = registry.dry_run(
        validated.manifest,
        target_version="1.0.0",
        record_ids=("mem_ALPHA",),
    )
    assert identity.steps == ()
    assert identity.warnings == ("no_version_change",)
    multihop = registry.dry_run(
        validated.manifest,
        target_version="2.0.0",
        record_ids=("mem_ALPHA",),
    )
    assert tuple(item.step_id for item in multihop.steps) == ("step-1", "step-2")
    with pytest.raises(ValueError, match="must not be blank"):
        registry.dry_run(validated.manifest, target_version=" ", record_ids=())
    with pytest.raises(ValueError, match="must be unique"):
        registry.dry_run(
            validated.manifest,
            target_version="2.0.0",
            record_ids=("mem_ALPHA", "mem_ALPHA"),
        )
    with pytest.raises(MigrationPlanningError, match="no registered migration path"):
        registry.dry_run(
            validated.manifest,
            target_version="9.0.0",
            record_ids=("mem_ALPHA",),
        )
    with pytest.raises(ValueError, match="transitions must be unique"):
        MigrationRegistry(
            (
                first,
                first.model_copy(update={"step_id": "different-step"}),
            )
        )
    with pytest.raises(ValueError, match="step IDs must be unique"):
        MigrationRegistry(
            (
                first,
                first.model_copy(update={"source_version": "2.0.0", "target_version": "3.0.0"}),
            )
        )
