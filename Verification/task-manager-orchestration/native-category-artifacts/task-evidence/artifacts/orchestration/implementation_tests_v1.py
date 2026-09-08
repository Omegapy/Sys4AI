"""Behavioral checks for the exact manager-assigned version-2 proposal."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from ticket_ordering import order_tickets


class OrderTicketsTests(unittest.TestCase):
    def assert_valid_order(self, records, expected_ids):
        snapshot = deepcopy(records)
        original_records = tuple(records)
        result = order_tickets(records)
        self.assertIsInstance(result, list)
        self.assertIsNot(result, records)
        self.assertEqual([record["id"] for record in result], expected_ids)
        self.assertEqual(len(result), len(original_records))
        by_id = {record["id"]: record for record in original_records}
        for record, expected_id in zip(result, expected_ids):
            self.assertIs(record, by_id[expected_id])
        self.assertEqual(len({id(record) for record in result}), len(result))
        self.assertEqual(records, snapshot)
        for current, original in zip(records, original_records):
            self.assertIs(current, original)
        return result

    def assert_invalid_preserved(self, records):
        snapshot = deepcopy(records)
        original_records = tuple(records) if isinstance(records, (list, tuple)) else None
        with self.assertRaises(ValueError) as caught:
            order_tickets(records)
        self.assertEqual(records, snapshot)
        if original_records is not None:
            self.assertEqual(len(records), len(original_records))
            for current, original in zip(records, original_records):
                self.assertIs(current, original)
        return str(caught.exception)

    def test_exact_fixture(self):
        fixture = Path(__file__).resolve().parents[1] / "data" / "tickets.json"
        records = json.loads(fixture.read_text())
        self.assertEqual([record["id"] for record in records], ["t3", "t1", "t2", "t4"])
        result = self.assert_valid_order(records, ["t1", "t3", "t2", "t4"])
        self.assertEqual([record["urgency"] for record in result], [3, 2, 2, 0])

    def test_empty_and_singleton_boundaries(self):
        self.assert_valid_order([], [])
        for urgency in (0, 3):
            with self.subTest(urgency=urgency):
                self.assert_valid_order([{"id": "one", "urgency": urgency}], ["one"])

    def test_all_four_urgency_values(self):
        records = [
            {"id": "zero", "urgency": 0},
            {"id": "two", "urgency": 2},
            {"id": "one", "urgency": 1},
            {"id": "three", "urgency": 3},
        ]
        self.assert_valid_order(records, ["three", "two", "one", "zero"])

    def test_all_equal_ties_preserve_non_alphabetical_ids(self):
        records = [{"id": value, "urgency": 2} for value in ("z", "a", "m")]
        self.assert_valid_order(records, ["z", "a", "m"])

    def test_mixed_ties(self):
        records = [
            {"id": "b", "urgency": 2},
            {"id": "z", "urgency": 3},
            {"id": "a", "urgency": 2},
            {"id": "low", "urgency": 0},
            {"id": "y", "urgency": 3},
        ]
        self.assert_valid_order(records, ["z", "y", "b", "a", "low"])

    def test_already_ordered_input_still_returns_new_list(self):
        records = [
            {"id": "top", "urgency": 3},
            {"id": "middle", "urgency": 1},
            {"id": "bottom", "urgency": 0},
        ]
        self.assert_valid_order(records, ["top", "middle", "bottom"])

    def test_nested_extras_and_raw_ids_are_preserved(self):
        nested = {"tags": ["urgent", {"urgency": 999}], "details": {"owner": "first"}}
        records = [
            {"id": "x", "urgency": 1, "extra": nested},
            {"id": "X", "urgency": 3, "extra": {"sort": -100}},
            {"id": " x ", "urgency": 1, "extra": ["do not normalize"]},
        ]
        tags = nested["tags"]
        details = nested["details"]
        result = self.assert_valid_order(records, ["X", "x", " x "])
        self.assertIs(result[1]["extra"], nested)
        self.assertIs(nested["tags"], tags)
        self.assertIs(nested["details"], details)

    def test_non_list_containers_are_rejected(self):
        for records in (None, (), ({"id": "x", "urgency": 1},), "records", {}, 7, True):
            with self.subTest(records=records):
                message = self.assert_invalid_preserved(records)
                self.assertIn("records", message)

    def test_malformed_records_after_valid_prefix(self):
        for malformed in (None, [], (), "ticket", 1, True):
            with self.subTest(malformed=malformed):
                records = [{"id": "first", "urgency": 0}, malformed, {"id": "last", "urgency": 3}]
                message = self.assert_invalid_preserved(records)
                self.assertIn("1", message)
                self.assertIn("dictionary", message)

    def test_missing_fields_after_valid_prefix(self):
        for malformed, missing in (({}, "id"), ({"urgency": 2}, "id"), ({"id": "x"}, "urgency")):
            with self.subTest(malformed=malformed):
                message = self.assert_invalid_preserved([{"id": "first", "urgency": 3}, malformed])
                self.assertIn("1", message)
                self.assertIn(missing, message)
                self.assertIn("missing", message)

    def test_invalid_ids(self):
        for ticket_id in (None, 1, True, [], {}, "", " \t\n"):
            with self.subTest(ticket_id=ticket_id):
                message = self.assert_invalid_preserved([{"id": ticket_id, "urgency": 3}])
                self.assertIn("id", message)

    def test_duplicate_ids_and_repeated_references(self):
        first = {"id": "repeat", "urgency": 1, "nested": {"values": [1, 2]}}
        for later in ({"id": "repeat", "urgency": 3}, first):
            with self.subTest(repeated_reference=later is first):
                records = [{"id": "prefix", "urgency": 0}, first, later]
                message = self.assert_invalid_preserved(records)
                self.assertIn("2", message)
                self.assertIn("id", message)
                self.assertIn("duplicate", message)

    def test_invalid_urgencies_alone_and_after_valid_prefix(self):
        for urgency in (True, False, -1, 4, 1.0, "2", None):
            for prefixed in (False, True):
                with self.subTest(urgency=urgency, prefixed=prefixed):
                    invalid = {"id": "invalid", "urgency": urgency, "nested": {"values": [1, 2]}}
                    records = [invalid]
                    if prefixed:
                        records = [{"id": "first", "urgency": 0}, invalid, {"id": "last", "urgency": 3}]
                    nested = invalid["nested"]
                    message = self.assert_invalid_preserved(records)
                    self.assertIn("urgency", message)
                    self.assertIs(invalid["nested"], nested)

    def test_compound_duplicate_and_boolean_defect(self):
        records = [
            {"id": "repeat", "urgency": 0},
            {"id": "repeat", "urgency": True, "extra": {"preserve": [1, 2]}},
            {"id": "tail", "urgency": False},
        ]
        self.assert_invalid_preserved(records)

    def test_diagnostics_identify_first_defective_record(self):
        records = [
            {"id": "first", "urgency": 0},
            {"id": "bad-urgency", "urgency": None},
            {"id": "", "urgency": 2},
        ]
        message = self.assert_invalid_preserved(records)
        self.assertIn("records[1]", message)
        self.assertIn("urgency", message)
        self.assertNotIn("records[2]", message)

    def test_missing_key_precedes_field_value_validation(self):
        message = self.assert_invalid_preserved([{"id": ""}])
        self.assertIn("missing", message)
        self.assertIn("urgency", message)
        self.assertNotIn("nonblank", message)


if __name__ == "__main__":
    unittest.main()
