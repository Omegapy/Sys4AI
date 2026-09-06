"""Versioned, non-mutating migration planning for neutral packages."""

from __future__ import annotations

from collections import deque

from sys4ai_memory.util import canonical_json_bytes, sha256_bytes

from .models import MemoryPackageManifest, MigrationDryRun, MigrationStep


class MigrationPlanningError(ValueError):
    """No explicit deterministic migration path satisfies the request."""


class MigrationRegistry:
    """Closed registry of reviewed package-version transitions."""

    def __init__(self, steps: tuple[MigrationStep, ...] = ()) -> None:
        identities = tuple((item.source_version, item.target_version) for item in steps)
        if len(identities) != len(set(identities)):
            raise ValueError("migration transitions must be unique")
        if len(tuple(item.step_id for item in steps)) != len(set(item.step_id for item in steps)):
            raise ValueError("migration step IDs must be unique")
        self._steps = tuple(sorted(steps, key=lambda item: item.step_id))

    def dry_run(
        self,
        manifest: MemoryPackageManifest,
        *,
        target_version: str,
        record_ids: tuple[str, ...],
    ) -> MigrationDryRun:
        """Report a deterministic path and impact without transforming bytes."""

        if not target_version.strip():
            raise ValueError("target_version must not be blank")
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("migration record IDs must be unique")
        source_version = manifest.package_version
        path = self._path(source_version, target_version)
        warnings = (
            ("no_version_change",)
            if source_version == target_version
            else (
                "dry_run_only_no_package_bytes_changed",
                "production_archive_and_encryption_selection_unresolved",
            )
        )
        affected = () if source_version == target_version else tuple(sorted(record_ids))
        payload = {
            "package_id": manifest.package_id,
            "source_version": source_version,
            "target_version": target_version,
            "steps": [item.model_dump(mode="json") for item in path],
            "affected_record_ids": affected,
            "warnings": warnings,
        }
        return MigrationDryRun(
            package_id=manifest.package_id,
            source_version=source_version,
            target_version=target_version,
            steps=path,
            affected_record_ids=affected,
            warnings=warnings,
            impact_digest=sha256_bytes(canonical_json_bytes(payload)),
        )

    def _path(self, source: str, target: str) -> tuple[MigrationStep, ...]:
        if source == target:
            return ()
        by_source: dict[str, list[MigrationStep]] = {}
        for step in self._steps:
            by_source.setdefault(step.source_version, []).append(step)
        queue: deque[tuple[str, tuple[MigrationStep, ...]]] = deque([(source, ())])
        visited = {source}
        while queue:
            current, path = queue.popleft()
            for step in sorted(by_source.get(current, ()), key=lambda item: item.step_id):
                candidate = (*path, step)
                if step.target_version == target:
                    return candidate
                if step.target_version not in visited:
                    visited.add(step.target_version)
                    queue.append((step.target_version, candidate))
        raise MigrationPlanningError(f"no registered migration path from {source!r} to {target!r}")
