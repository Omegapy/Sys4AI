from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from tools.validate_dependency_upgrade import (
    REQUIRED_CHECKS,
    validate_dependency_upgrade_review,
)


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _review(baseline: bytes, candidate: bytes) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "candidate": {
            "candidate_id": "upgrade-cognee-1-5-4",
            "package": "cognee",
            "from_version": "1.5.3",
            "to_version": "1.5.4",
            "reason": "Evaluate the next pinned provider release.",
            "python_version": "3.12.11",
            "baseline_lock_sha256": _digest(baseline),
            "candidate_lock_sha256": _digest(candidate),
        },
        "upstream_review": {
            "release_notes_ref": "evidence/release-notes.md",
            "package_metadata_ref": "evidence/package-metadata.md",
            "license_ref": "evidence/license-review.md",
            "security_advisory_ref": "evidence/security-review.md",
            "transitive_change_summary": "Reviewed candidate dependency changes.",
        },
        "platforms": [
            {
                "platform": "macos-arm64",
                "lock_resolved": True,
                "smoke_suite_passed": True,
                "evidence": "receipt:macos-smoke",
            },
            {
                "platform": "linux-x86_64",
                "lock_resolved": True,
                "smoke_suite_passed": True,
                "evidence": "receipt:linux-smoke",
            },
        ],
        "checks": [
            {
                "check_id": check_id,
                "passed": True,
                "evidence": f"receipt:{check_id}",
            }
            for check_id in sorted(REQUIRED_CHECKS)
        ],
        "migration_review": {
            "required": True,
            "status": "passed",
            "dry_run_completed": True,
            "prior_generation_preserved": True,
            "evidence": "receipt:migration-dry-run",
        },
        "rollback": {
            "baseline_lock_ref": "accepted/uv.lock",
            "prior_generation_ref": "generation:accepted",
            "verified": True,
            "evidence": "receipt:rollback-recovery",
        },
        "decision": {
            "status": "accepted",
            "reviewer": "release-reviewer",
            "reviewed_at": "2026-09-03T19:30:00-06:00",
            "rationale": "All required compatibility and migration checks passed.",
        },
    }


def _write_case(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, object]]:
    baseline_bytes = b"baseline lock\n"
    candidate_bytes = b"candidate lock\n"
    baseline = tmp_path / "baseline.lock"
    candidate = tmp_path / "candidate.lock"
    review = tmp_path / "review.json"
    baseline.write_bytes(baseline_bytes)
    candidate.write_bytes(candidate_bytes)
    payload = _review(baseline_bytes, candidate_bytes)
    review.write_text(json.dumps(payload), encoding="utf-8")
    return review, baseline, candidate, payload


def test_complete_upgrade_review_binds_checks_migration_platforms_and_locks(
    tmp_path: Path,
) -> None:
    review, baseline, candidate, _ = _write_case(tmp_path)

    result = validate_dependency_upgrade_review(
        review,
        baseline_lock_path=baseline,
        candidate_lock_path=candidate,
    )

    assert result["valid"] is True
    assert result["candidate_accepted"] is True
    assert result["decision_status"] == "accepted"
    assert result["required_check_count"] == len(REQUIRED_CHECKS)


def test_missing_check_and_platform_fail_closed(tmp_path: Path) -> None:
    review, baseline, candidate, payload = _write_case(tmp_path)
    altered = deepcopy(payload)
    altered["checks"] = altered["checks"][1:]  # type: ignore[index]
    altered["platforms"] = altered["platforms"][:1]  # type: ignore[index]
    review.write_text(json.dumps(altered), encoding="utf-8")

    result = validate_dependency_upgrade_review(
        review,
        baseline_lock_path=baseline,
        candidate_lock_path=candidate,
    )

    assert result["valid"] is False
    assert any("missing required checks" in error for error in result["errors"])
    assert any("missing supported platform" in error for error in result["errors"])


def test_cognee_review_cannot_skip_migration_or_rollback(tmp_path: Path) -> None:
    review, baseline, candidate, payload = _write_case(tmp_path)
    altered = deepcopy(payload)
    altered["migration_review"] = {
        "required": False,
        "status": "not_required",
        "dry_run_completed": False,
        "prior_generation_preserved": False,
        "evidence": "claimed unnecessary",
    }
    altered["rollback"]["verified"] = False  # type: ignore[index]
    review.write_text(json.dumps(altered), encoding="utf-8")

    result = validate_dependency_upgrade_review(
        review,
        baseline_lock_path=baseline,
        candidate_lock_path=candidate,
    )

    assert result["valid"] is False
    assert result["candidate_accepted"] is False


def test_review_is_bound_to_exact_lock_bytes_and_rejects_secret_like_content(
    tmp_path: Path,
) -> None:
    review, baseline, candidate, payload = _write_case(tmp_path)
    candidate.write_bytes(b"different candidate lock\n")
    mismatched = validate_dependency_upgrade_review(
        review,
        baseline_lock_path=baseline,
        candidate_lock_path=candidate,
    )
    assert mismatched["valid"] is False
    assert any("candidate lock digest" in error for error in mismatched["errors"])

    altered = deepcopy(payload)
    altered["decision"]["rationale"] = "api_key=" + "runtime-only-value"  # type: ignore[index]
    review.write_text(json.dumps(altered), encoding="utf-8")
    secret = validate_dependency_upgrade_review(
        review,
        baseline_lock_path=baseline,
        candidate_lock_path=candidate,
    )
    assert secret["valid"] is False
    assert secret["errors"] == ["upgrade review contains prohibited secret-like content"]
    assert "runtime-only-value" not in json.dumps(secret)
