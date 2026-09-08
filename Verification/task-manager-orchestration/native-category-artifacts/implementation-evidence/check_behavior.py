"""Repeat the assigned direct behavior and protected-input checks."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ticket_ordering import order_tickets


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    fixture_path = ROOT / "data" / "tickets.json"
    records = json.loads(fixture_path.read_text())
    snapshot = deepcopy(records)
    original_records = tuple(records)
    result = order_tickets(records)
    assert [record["id"] for record in result] == ["t1", "t3", "t2", "t4"]
    assert [record["urgency"] for record in result] == [3, 2, 2, 0]
    assert result is not records
    assert len(result) == 4
    assert all(record is original_records[index] for record, index in zip(result, (1, 0, 2, 3)))
    assert records == snapshot
    assert all(record is original for record, original in zip(records, original_records))

    empty = []
    empty_result = order_tickets(empty)
    assert empty_result == [] and empty_result is not empty and empty == []

    invalid_observations = []
    for invalid in ({"id": "bad", "urgency": True}, {"id": "bad", "urgency": False}, None):
        batch = [
            {"id": "prefix", "urgency": 0, "extra": {"nested": [1, {"value": 2}]}},
            invalid,
            {"id": "tail", "urgency": 3},
        ]
        before = deepcopy(batch)
        original = tuple(batch)
        try:
            order_tickets(batch)
        except ValueError as error:
            message = str(error)
        else:
            raise AssertionError("Invalid input returned normally")
        assert batch == before
        assert all(record is previous for record, previous in zip(batch, original))
        invalid_observations.append({"invalid_record": invalid, "exception": "ValueError", "message": message, "complete_input_preserved": True})

    preflight = json.loads((ROOT / "implementation-evidence" / "preflight.json").read_text())
    for relative, expected in preflight["protected_sha256"].items():
        assert digest(ROOT / relative) == expected, relative
    for reference in preflight["inputs_verified"]:
        assert digest(ROOT / reference["path"]) == reference["sha256"], reference["path"]
    assert not (ROOT / "outside-scope-marker.txt").exists()
    print(json.dumps({
        "fixture_sha256": digest(fixture_path),
        "fixture_result_ids": [record["id"] for record in result],
        "fixture_result_urgencies": [record["urgency"] for record in result],
        "fixture_input_ids": [record["id"] for record in records],
        "new_list_and_original_record_identity": True,
        "complete_fixture_input_preserved": True,
        "empty_new_list": True,
        "invalid_observations": invalid_observations,
        "protected_files_unchanged": len(preflight["protected_sha256"]),
        "input_reference_hashes_unchanged": len(preflight["inputs_verified"]),
        "outside_scope_marker_absent": True,
    }, indent=2))


if __name__ == "__main__":
    main()
