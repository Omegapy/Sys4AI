from __future__ import annotations

import csv
from pathlib import Path

from tools.validate_release_evidence import DEFAULT_LEDGER, validate_ledger


def _copy_rows() -> list[dict[str, str]]:
    with DEFAULT_LEDGER.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return rows


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_current_release_ledger_matches_the_audited_evidence_distribution() -> None:
    result = validate_ledger()
    assert result["valid"] is True
    assert result["row_count"] == 296
    assert result["status_counts"] == {
        "deferred": 1,
        "implemented_unverified": 4,
        "runtime_verified": 7,
        "static_verified": 12,
        "targeted_tests_passed": 272,
    }


def test_duplicate_and_missing_ids_are_rejected(tmp_path: Path) -> None:
    rows = _copy_rows()
    rows[-1]["item_id"] = rows[0]["item_id"]
    candidate = tmp_path / "ledger.csv"
    _write_rows(candidate, rows)
    result = validate_ledger(candidate)
    assert result["valid"] is False
    assert any("duplicate item IDs" in error for error in result["errors"])
    assert any("missing item IDs" in error for error in result["errors"])


def test_evidence_state_requires_a_locator(tmp_path: Path) -> None:
    rows = _copy_rows()
    unresolved = next(row for row in rows if row["status"] == "implemented_unverified")
    unresolved["status"] = "targeted_tests_passed"
    unresolved["current_evidence"] = ""
    candidate = tmp_path / "ledger.csv"
    _write_rows(candidate, rows)
    result = validate_ledger(candidate)
    assert result["valid"] is False
    assert any("evidence state requires a locator" in error for error in result["errors"])
