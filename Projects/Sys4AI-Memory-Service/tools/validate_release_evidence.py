#!/usr/bin/env python3
"""Validate release-ledger identity, source lineage, and evidence-state rules."""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "docs/verification/release_evidence_ledger.csv"
REQUIRED_COLUMNS = (
    "item_id",
    "item_class",
    "source_document",
    "source_locator",
    "priority",
    "requirement_or_outcome",
    "plan_tasks",
    "implementation_expectation",
    "planned_verification",
    "status",
    "current_evidence",
)
NON_EVIDENCE_STATES = {"not_implemented", "decision_pending", "blocked", "deferred"}
EVIDENCE_STATES = {
    "implemented_unverified",
    "static_verified",
    "targeted_tests_passed",
    "broader_suite_passed",
    "runtime_verified",
    "end_to_end_verified",
}
ALLOWED_STATES = NON_EVIDENCE_STATES | EVIDENCE_STATES
LINE_LOCATOR = re.compile(r"\blines? (\d+)(?:-(\d+))?\b")


def expected_ids() -> set[str]:
    families = {
        "P": 15,
        "G": 12,
        "MEM-FR": 178,
        "MEM-NFR": 28,
        "AC": 12,
        "UC": 12,
        "MEM-DEC": 14,
        "MEM-OQ": 11,
        "DOD": 14,
    }
    return {
        f"{prefix}-{number:0{3 if prefix.startswith('MEM-') else 2}d}"
        for prefix, count in families.items()
        for number in range(1, count + 1)
    }


def validate_ledger(path: Path = DEFAULT_LEDGER) -> dict[str, object]:
    errors: list[str] = []
    if path.is_symlink() or not path.is_file():
        return {"valid": False, "errors": ["ledger must be a regular non-symlink file"]}
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
        errors.append("ledger columns do not match the versioned contract")

    identifiers = [row.get("item_id", "") for row in rows]
    duplicates = sorted(item for item, count in Counter(identifiers).items() if count > 1)
    if duplicates:
        errors.append(f"duplicate item IDs: {', '.join(duplicates)}")
    expected = expected_ids()
    observed = set(identifiers)
    if missing := sorted(expected - observed):
        errors.append(f"missing item IDs: {', '.join(missing)}")
    if extra := sorted(observed - expected):
        errors.append(f"unexpected item IDs: {', '.join(extra)}")

    for row_number, row in enumerate(rows, start=2):
        identifier = row.get("item_id", "")
        status = row.get("status", "")
        evidence = row.get("current_evidence", "").strip()
        if status not in ALLOWED_STATES:
            errors.append(f"row {row_number} {identifier}: invalid status {status!r}")
        if status in EVIDENCE_STATES and not evidence:
            errors.append(f"row {row_number} {identifier}: evidence state requires a locator")
        if status in {"not_implemented", "decision_pending"} and evidence:
            errors.append(f"row {row_number} {identifier}: pending state cannot claim evidence")

        source_value = row.get("source_document", "")
        source = ROOT / source_value
        if source.is_symlink():
            errors.append(f"row {row_number} {identifier}: source cannot be a symlink")
            continue
        try:
            source.resolve(strict=True).relative_to(ROOT.resolve(strict=True))
        except (FileNotFoundError, ValueError):
            errors.append(f"row {row_number} {identifier}: source is missing or outside project")
            continue
        match = LINE_LOCATOR.search(row.get("source_locator", ""))
        if not match:
            errors.append(f"row {row_number} {identifier}: source locator lacks a line")
            continue
        start = int(match.group(1))
        end = int(match.group(2) or start)
        lines = source.read_text(encoding="utf-8").splitlines()
        if start < 1 or end < start or end > len(lines):
            errors.append(f"row {row_number} {identifier}: source line range is invalid")
            continue
        source_excerpt = "\n".join(lines[start - 1 : end])
        if not identifier.startswith("DOD-") and identifier not in source_excerpt:
            errors.append(f"row {row_number} {identifier}: identifier absent from source range")

    return {
        "valid": not errors,
        "row_count": len(rows),
        "status_counts": dict(sorted(Counter(row.get("status", "") for row in rows).items())),
        "errors": errors,
    }


def main() -> int:
    result = validate_ledger()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
