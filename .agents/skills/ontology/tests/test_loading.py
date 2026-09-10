import copy
import os
from pathlib import Path
import tempfile
import unittest
from support import make_project, read_json, write_json, add_records, record, sha256
from ontology_core import load_project, OntologyError, read_bytes, safe_path


class LoadingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = make_project(Path(self.temp.name) / "project")

    def test_neutral_identity_and_current_saved_identity_rejected(self):
        config = read_json(self.root / "ontology.yaml")
        config["project"]["id"] = None
        write_json(self.root / "ontology.yaml", config)
        with self.assertRaisesRegex(OntologyError, "Specialize"): load_project(self.root)
        self.root = make_project(self.root)
        write_json(self.root / "project.json", {"project_id": "different"})
        with self.assertRaises(OntologyError): load_project(self.root)

    def test_duplicate_json_keys_and_nonfinite_numbers_rejected(self):
        for text in ('{"schema_version":1,"schema_version":1}', '{"x":NaN}'):
            (self.root / "ontology.yaml").write_text(text)
            with self.assertRaises(OntologyError): load_project(self.root)

    def test_remote_context_and_unknown_profile_keys_rejected(self):
        path = self.root / "ONTOLOGY/modules/project/project.jsonld"
        value = read_json(path)
        value["@context"] = "https://invalid.example/context"
        write_json(path, value)
        with self.assertRaises(OntologyError) as error: load_project(self.root)
        self.assertEqual(error.exception.code, "untrusted_context")
        value["@context"] = "ONTOLOGY/contexts/context-v1.jsonld"
        value["@graph"] = [{**record("bad"), "@reverse": {}}]
        write_json(path, value)
        with self.assertRaises(OntologyError) as error: load_project(self.root)
        self.assertEqual(error.exception.code, "unsupported_profile")

    def test_paths_symlinks_hardlinks_and_fifo_fail_without_reading_target(self):
        with self.assertRaises(OntologyError): safe_path(self.root, "../secret")
        with self.assertRaises(OntologyError): safe_path(self.root, "/etc/passwd")
        (self.root / "alias").symlink_to(self.root / "SPECS.md")
        with self.assertRaises(OntologyError): safe_path(self.root, "alias")
        os.link(self.root / "SPECS.md", self.root / "hardlink")
        with self.assertRaises(OntologyError): read_bytes(self.root / "hardlink")
        os.mkfifo(self.root / "pipe")
        with self.assertRaises(OntologyError): read_bytes(self.root / "pipe")

    def test_unselected_and_child_sources_rejected(self):
        for path in ("unselected.md", "Projects/child/SPECS.md", "projects/child/SPECS.md", ".env", ".sys4ai/state.json", ".VENV/secret.txt", "ontology/wiki/Task.md"):
            r = record("source")
            r["sources"][0]["path"] = path
            target = self.root / "ONTOLOGY/modules/project/project.jsonld"
            value = read_json(target); value["@graph"] = [r]; write_json(target, value)
            with self.assertRaises(OntologyError): load_project(self.root)

    def test_reads_are_isolated_and_do_not_create_state(self):
        add_records(self.root, [record("shared-label", label="Same label")])
        second = make_project(Path(self.temp.name) / "second", project_id="second")
        add_records(second, [record("shared-label", identity="second", label="Same label")])
        before = {p.relative_to(self.root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()}
        first, other = load_project(self.root), load_project(second)
        self.assertNotEqual(first.namespace, other.namespace)
        self.assertEqual(before, {p.relative_to(self.root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()})
        self.assertFalse((self.root / ".sys4ai").exists())

    def test_malformed_nested_shapes_return_bounded_profile_diagnostics(self):
        target = self.root / "ONTOLOGY/modules/project/project.jsonld"
        value = read_json(target)
        for key, wrong in (("kind", []), ("lifecycle", []), ("@type", [{}]), ("replacement", {}), ("ambiguity_with", [None]), ("domain", {})):
            value["@graph"] = [{**record("malformed"), key: wrong}]
            write_json(target, value)
            with self.subTest(key=key):
                with self.assertRaises(OntologyError) as error: load_project(self.root)
                self.assertLess(len(error.exception.message), 1000)

    def test_configuration_boolean_schema_and_nested_file_lists_are_rejected(self):
        original = read_json(self.root / "ontology.yaml")
        for key, value in (("schema_version", True), ("project_files", [{}]), ("source_allowlist", [[]])):
            config = copy.deepcopy(original); config[key] = value
            write_json(self.root / "ontology.yaml", config)
            with self.subTest(key=key):
                with self.assertRaises(OntologyError): load_project(self.root)

    def test_stale_and_missing_sources_have_explicit_freshness(self):
        add_records(self.root, [record("bound-artifact")])
        (self.root / "SPECS.md").write_text("Changed source\n")
        project = load_project(self.root)
        self.assertEqual(next(s for s in project.sources if s["path"] == "SPECS.md")["status"], "stale")
        (self.root / "SPECS.md").unlink()
        self.assertEqual(next(s for s in load_project(self.root).sources if s["path"] == "SPECS.md")["status"], "unavailable")


if __name__ == "__main__": unittest.main()
