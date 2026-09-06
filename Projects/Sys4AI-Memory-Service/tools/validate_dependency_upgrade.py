#!/usr/bin/env python3
"""Validate a dependency-upgrade review against the exact lock artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from sys4ai_memory.security import SecretDetectedError, require_secret_free
from sys4ai_memory.util import sha256_file

REQUIRED_CHECKS = frozenset(
    {
        "configuration",
        "contracts",
        "exchange",
        "integration",
        "interfaces",
        "lock_resolution",
        "migration",
        "observability",
        "profiles",
        "provider",
        "rebuild",
        "rollback",
        "security",
        "static_analysis",
    }
)
REQUIRED_PLATFORM_FAMILIES = frozenset({"linux", "macos"})
MAX_REVIEW_BYTES = 1024 * 1024


class ReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class CandidateIdentity(ReviewModel):
    candidate_id: str = Field(min_length=1)
    package: str = Field(min_length=1)
    from_version: str = Field(min_length=1)
    to_version: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    python_version: str = Field(pattern=r"^3\.12(?:\.[0-9]+)?$")
    baseline_lock_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_lock_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class UpstreamReview(ReviewModel):
    release_notes_ref: str = Field(min_length=1)
    package_metadata_ref: str = Field(min_length=1)
    license_ref: str = Field(min_length=1)
    security_advisory_ref: str = Field(min_length=1)
    transitive_change_summary: str = Field(min_length=1)


class PlatformResult(ReviewModel):
    platform: str = Field(pattern=r"^(?:linux|macos)-[A-Za-z0-9_.-]+$")
    lock_resolved: bool
    smoke_suite_passed: bool
    evidence: str = Field(min_length=1)


class CheckResult(ReviewModel):
    check_id: str = Field(min_length=1)
    passed: bool
    evidence: str = Field(min_length=1)


class MigrationReview(ReviewModel):
    required: bool
    status: Literal["passed", "failed", "not_required"]
    dry_run_completed: bool
    prior_generation_preserved: bool
    evidence: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_status(self) -> Self:
        if self.required and self.status == "not_required":
            raise ValueError("a required migration review cannot be marked not_required")
        if not self.required and self.status != "not_required":
            raise ValueError("an optional migration review must be marked not_required")
        if self.status == "passed" and (
            not self.dry_run_completed or not self.prior_generation_preserved
        ):
            raise ValueError(
                "a passed migration review requires a dry run and preserved prior generation"
            )
        return self


class RollbackReview(ReviewModel):
    baseline_lock_ref: str = Field(min_length=1)
    prior_generation_ref: str = Field(min_length=1)
    verified: bool
    evidence: str = Field(min_length=1)


class ReviewDecision(ReviewModel):
    status: Literal["accepted", "rejected"]
    reviewer: str = Field(min_length=1)
    reviewed_at: datetime
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_timezone(self) -> Self:
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise ValueError("reviewed_at must include a timezone")
        return self


class DependencyUpgradeReview(ReviewModel):
    schema_version: Literal["1.0"] = "1.0"
    candidate: CandidateIdentity
    upstream_review: UpstreamReview
    platforms: tuple[PlatformResult, ...] = Field(min_length=1)
    checks: tuple[CheckResult, ...] = Field(min_length=1)
    migration_review: MigrationReview
    rollback: RollbackReview
    decision: ReviewDecision

    @model_validator(mode="after")
    def validate_review(self) -> Self:
        platform_ids = tuple(item.platform for item in self.platforms)
        if len(platform_ids) != len(set(platform_ids)):
            raise ValueError("platform results must be unique")
        check_ids = tuple(item.check_id for item in self.checks)
        if len(check_ids) != len(set(check_ids)):
            raise ValueError("upgrade checks must be unique")
        if self.candidate.package.casefold() == "cognee" and not self.migration_review.required:
            raise ValueError("Cognee upgrades require a storage migration review")
        if self.decision.status == "accepted":
            if not all(item.lock_resolved and item.smoke_suite_passed for item in self.platforms):
                raise ValueError("an accepted candidate requires passing platform results")
            if not all(item.passed for item in self.checks):
                raise ValueError("an accepted candidate requires every compatibility check")
            if self.migration_review.required and self.migration_review.status != "passed":
                raise ValueError("an accepted candidate requires a passed migration review")
            if not self.rollback.verified:
                raise ValueError("an accepted candidate requires verified rollback evidence")
        return self


def _load_review(path: Path) -> dict[str, JsonValue]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("upgrade review must be a regular non-symlink file")
    if path.stat().st_size > MAX_REVIEW_BYTES:
        raise ValueError("upgrade review exceeds the one MiB limit")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("upgrade review must contain one JSON object")
    return value


def _lock_digest(path: Path, label: str) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} lock must be a regular non-symlink file")
    return sha256_file(path)


def validate_dependency_upgrade_review(
    review_path: Path,
    *,
    baseline_lock_path: Path,
    candidate_lock_path: Path,
) -> dict[str, object]:
    """Return a stable, secret-free validation result for one upgrade review."""

    errors: list[str] = []
    review: DependencyUpgradeReview | None = None
    baseline_digest: str | None = None
    candidate_digest: str | None = None
    try:
        raw = _load_review(review_path)
        require_secret_free(raw, field_path="dependency_upgrade_review")
        review = DependencyUpgradeReview.model_validate(raw)
        baseline_digest = _lock_digest(baseline_lock_path, "baseline")
        candidate_digest = _lock_digest(candidate_lock_path, "candidate")
    except SecretDetectedError:
        errors.append("upgrade review contains prohibited secret-like content")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        errors.append(str(error))

    if review is not None and baseline_digest is not None and candidate_digest is not None:
        if review.candidate.baseline_lock_sha256 != baseline_digest:
            errors.append("baseline lock digest does not match the reviewed artifact")
        if review.candidate.candidate_lock_sha256 != candidate_digest:
            errors.append("candidate lock digest does not match the reviewed artifact")
        if (
            review.candidate.from_version != review.candidate.to_version
            and baseline_digest == candidate_digest
        ):
            errors.append("a version change requires a distinct candidate lock artifact")
        observed_checks = {item.check_id for item in review.checks}
        missing_checks = sorted(REQUIRED_CHECKS - observed_checks)
        unknown_checks = sorted(observed_checks - REQUIRED_CHECKS)
        if missing_checks:
            errors.append("missing required checks: " + ", ".join(missing_checks))
        if unknown_checks:
            errors.append("unknown upgrade checks: " + ", ".join(unknown_checks))
        families = {item.platform.split("-", 1)[0] for item in review.platforms}
        missing_platforms = sorted(REQUIRED_PLATFORM_FAMILIES - families)
        if missing_platforms:
            errors.append(
                "missing supported platform results: " + ", ".join(missing_platforms)
            )

    decision_status = None if review is None else review.decision.status
    return {
        "valid": not errors,
        "errors": errors,
        "decision_status": decision_status,
        "candidate_accepted": not errors and decision_status == "accepted",
        "baseline_lock_sha256": baseline_digest,
        "candidate_lock_sha256": candidate_digest,
        "required_check_count": len(REQUIRED_CHECKS),
        "required_platform_families": sorted(REQUIRED_PLATFORM_FAMILIES),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--baseline-lock", type=Path, required=True)
    parser.add_argument("--candidate-lock", type=Path, required=True)
    return parser


def main(argv: tuple[str, ...] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = validate_dependency_upgrade_review(
        args.review,
        baseline_lock_path=args.baseline_lock,
        candidate_lock_path=args.candidate_lock,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
