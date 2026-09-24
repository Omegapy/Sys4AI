"""Snapshot-only deterministic acceptance. All writers target disposable roots.

No browser/service/resource-supervisor claim is made by these tests. The reader
semantic validator in callback tests is a deliberately bounded test validator;
complete presentation/source/process semantics remain the reader adapter's gate.
"""
from pathlib import Path
import copy
import fcntl
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from support import (PACKAGE, bind_director, canonical_bytes, fixture_context,
                     grant, make_project, project_id, proposal, read_json, record,
                     sha256, write_json)
from explorer_support import make_explorer_project
from ontology_core import load_project, operation_lock
from ontology_publication import publish, recover, integration_preview, integration_publish, integration_recover
from ontology_explorer_snapshot import open_store
from test_curator_integration import fixture as integration_fixture, integration_grant

SCHEMA = fixture_context()["contracts"] / "schema/explorer-v1.json"


def inventory(root):
    return {p.relative_to(root).as_posix(): (sha256(p), p.stat().st_mtime_ns, p.stat().st_size)
            for p in sorted(root.rglob("*")) if p.is_file()}


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = make_project(self.base / "project")
        self.scripts = self.base / "frozen-scripts"
        self.scripts.mkdir()
        for p in (PACKAGE / "scripts").glob("ontology*.py"):
            shutil.copyfile(p, self.scripts / p.name)
        self.stores = []
        self.addCleanup(self.close_stores)

    def close_stores(self):
        for store in self.stores:
            if not store._readers: store.close()

    def store(self, root=None, **kw):
        kw.setdefault("scripts", self.scripts)
        store = open_store(root or self.root, schema_path=kw.pop("schema_path", SCHEMA), **kw)
        self.stores.append(store)
        return store

    def assert_code(self, code, function):
        try: function()
        except ValueError as exc:
            self.assertEqual(getattr(exc, "code", None), code, repr(exc))
            self.assertLess(len(str(exc)), 160)
            self.assertNotIn(str(self.root), str(exc))
            return exc
        self.fail("Expected " + code)

    def read(self, store, **kw):
        with store.lease(**kw) as view: return view

    def authored(self):
        cfg = read_json(self.root / "ontology.yaml")
        write_json(self.root / cfg["project_files"][0], {"@context": cfg["context"]["path"], "@graph": [record("one")]})
        return self.root / cfg["project_files"][0]

    def change_definition(self, target, text):
        data = read_json(target); data["@graph"][0]["definition"] = text; write_json(target, data)

    def test_no_read_writes_and_deep_immutable_cache(self):
        self.authored(); before = inventory(self.root); store = self.store()
        first = self.read(store); second = self.read(store)
        self.assertIs(first, second)
        self.assertEqual(before, inventory(self.root))
        self.assertFalse((self.root / "control_records").exists())
        self.assertFalse((self.root / ".sys4ai").exists())
        with self.assertRaises(TypeError): first.project.by_id[project_id("one")]["definition"] = "edit"
        with self.assertRaises(TypeError): first.manifest["files"]["ontology.yaml"]["sha256"] = "0"*64
        with self.assertRaises((AttributeError, TypeError)): first.project.records += ()
        self.assertEqual(first.project.context()["helpers"], store.package.helpers)
        self.assertEqual(set(store.package.loaded_digests), {"ontology_core", "ontology_modules", "ontology_validate", "ontology_explorer_snapshot"})
        self.assertFalse(any("publication" in k or "integration" in k for k in store.package.modules))

    def test_stale_and_missing_sources_preserve_recorded_definition(self):
        self.authored(); store = self.store(); first = self.read(store)
        recorded = first.project.by_id[project_id("one")]["definition"]
        (self.root / "SPECS.md").write_text("Changed evidence\n")
        stale = self.read(store)
        self.assertNotEqual(first.snapshot_id, stale.snapshot_id)
        self.assertEqual(recorded, stale.project.by_id[project_id("one")]["definition"])
        self.assertIn("stale", {s["status"] for s in stale.project.sources})
        (self.root / "SPECS.md").unlink(); missing = self.read(store)
        self.assertEqual(recorded, missing.project.by_id[project_id("one")]["definition"])
        self.assertIn("unavailable", {s["status"] for s in missing.project.sources})
        self.assertEqual(self.read(store).snapshot_id, missing.snapshot_id)

    def test_unchanged_mtime_bytes_invalidate_expected_snapshot(self):
        target = self.authored(); store = self.store(); first = self.read(store)
        before = target.stat(); self.change_definition(target, "Changed definition.")
        os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assert_code("snapshot_changed", lambda: self.read(store, expected_snapshot=first.snapshot_id))
        self.assertEqual(self.read(store).project.by_id[project_id("one")]["definition"], "Changed definition.")

    def test_optional_identity_appearance_and_presentation_bytes_change(self):
        store = self.store(); first = self.read(store); cfg = read_json(self.root / "ontology.yaml")["project"]
        write_json(self.root / "project.json", {"project_id": cfg["id"], "project_name": cfg["name"], "purpose": cfg["purpose"]})
        second = self.read(store); self.assertNotEqual(first.snapshot_id, second.snapshot_id)
        write_json(self.root / "ontology-explorer.yaml", {"schema_version": 1, "project_id": "example", "limits": {"source_files": 10}})
        third = self.read(store); self.assertNotEqual(second.snapshot_id, third.snapshot_id)
        self.assertEqual(first.root_scope_id, third.root_scope_id)
        self.assertFalse((self.root / "control_records").exists())

    def test_invalid_canonical_and_presentation_preserve_previous_current(self):
        target = self.authored(); store = self.store(); first = self.read(store)
        data = read_json(target); data["@graph"][0]["@type"] = [project_id("missing")]; write_json(target, data)
        self.assert_code("canonical_invalid", lambda: self.read(store)); self.assertIs(store.current, first)
        self.authored()
        for raw in (b'{"schema_version":1,"project_id":"example","x":1}', b'{"schema_version":1,"project_id":"example","project_id":"example"}', b'{"schema_version":true,"project_id":"example"}'):
            (self.root / "ontology-explorer.yaml").write_bytes(raw)
            self.assert_code("presentation_invalid", lambda: self.read(store)); self.assertIs(store.current, first)

    def assert_malformed_preserves_current(self, store, first, path, values):
        original = path.read_bytes() if path.exists() else None
        for value in values:
            with self.subTest(path=path.relative_to(self.root).as_posix(), value=value):
                try:
                    write_json(path, value)
                    with self.assertRaises(store.error_type) as raised:
                        self.read(store)
                    self.assertEqual(raised.exception.code, "canonical_invalid")
                    self.assertEqual(str(raised.exception), "Selected canonical knowledge failed validation.")
                    self.assertIs(store.current, first)
                finally:
                    if original is None: path.unlink()
                    else: path.write_bytes(original)

    def test_malformed_module_manifest_containers_are_fixed_errors(self):
        store = self.store(); first = self.read(store)
        cfg = read_json(self.root / "ontology.yaml")
        path = self.root / cfg["modules"][0]["path"] / "manifest.json"
        original = read_json(path)
        malformed = [[], None, "manifest", {**original, "files": []},
                     {**original, "record_files": {}}, {**original, "record_files": [None]}]
        self.assert_malformed_preserves_current(store, first, path, malformed)
        self.assertIs(self.read(store), first)

    def test_malformed_graph_and_source_containers_are_fixed_errors(self):
        path = self.authored(); original = read_json(path)
        store = self.store(); first = self.read(store)
        malformed = [[], None, "graph", {**original, "@graph": {}}, {**original, "@graph": [[]]}]
        for sources in (None, {}, "sources", [None], [[]]):
            document = copy.deepcopy(original); document["@graph"][0]["sources"] = sources; malformed.append(document)
        self.assert_malformed_preserves_current(store, first, path, malformed)
        self.assertIs(self.read(store), first)

    def test_malformed_nested_config_and_identity_containers_are_fixed_errors(self):
        store = self.store(); first = self.read(store); path = self.root / "ontology.yaml"
        original = read_json(path); malformed = [[], None]
        for key in ("project", "context", "retrieval", "publication"):
            malformed.append({**original, key: []})
        for key in ("modules", "project_files", "binding_files", "source_allowlist", "competency_files"):
            malformed.append({**original, key: {}})
            malformed.append({**original, key: [None]})
        malformed.append({**original, "publication": {"enabled": False, "binding": []}})
        malformed.append({**original, "publication": {"enabled": False, "binding": {"actor_id": "fixture", "scope": [{}], "authority": []}}})
        self.assert_malformed_preserves_current(store, first, path, malformed)
        self.assert_malformed_preserves_current(store, first, self.root / "project.json", [[], None, "identity"])
        self.assert_malformed_preserves_current(store, first, self.root / "depot/projects.json", [[], None, {"projects": {}}, {"projects": [[]]}])
        # Removing newly introduced identity files leaves a new empty depot
        # directory observation, so only the canonical payload equality is asserted.
        self.assertEqual(self.read(store).project.records, first.project.records)

    def test_semantic_validator_runs_before_current_swap(self):
        target = self.authored(); calls = []
        def validate(view):
            calls.append(view.snapshot_id)
            for rid in (view.presentation or {}).get("starting_ids", ()):
                if rid not in view.project.by_id: raise ValueError("Invalid fixture selector")
        store = self.store(validate_view=validate); first = self.read(store)
        write_json(self.root / "ontology-explorer.yaml", {"schema_version": 1, "project_id": "example", "starting_ids": [project_id("missing")]})
        self.assert_code("presentation_invalid", lambda: self.read(store)); self.assertIs(store.current, first)
        self.assertEqual(len(calls), 2)
        unvalidated = self.store()
        self.assert_code("presentation_invalid", lambda: self.read(unvalidated))
        self.assertIsNone(unvalidated.current)

    def test_source_only_observation_does_not_advance_view_or_allow_canonical_change(self):
        target = self.authored(); store = self.store(); first = self.read(store)
        (self.root / "SPECS.md").write_text("Fresh evidence\n")
        body, marker = store.observe_source(first, "SPECS.md")
        self.assertEqual(body, b"Fresh evidence\n"); self.assertEqual(marker["sha256"], sha256(body)); self.assertIs(store.current, first)
        self.change_definition(target, "New canonical meaning")
        self.assert_code("snapshot_changed", lambda: store.observe_source(first, "SPECS.md"))
        self.assert_code("source_unavailable", lambda: store.observe_source(first, "unselected.txt"))
        other = self.store(make_project(self.base / "foreign"))
        self.assert_code("snapshot_changed", lambda: other.observe_source(first, "SPECS.md"))

    def test_two_view_lifetime_reader_failure_and_capacity(self):
        target = self.authored(); store = self.store()
        with store.lease() as first:
            self.change_definition(target, "Second definition")
            second = self.read(store); self.assertIs(store.retiring, first)
            self.assertNotEqual(first.snapshot_id, second.snapshot_id)
            self.change_definition(target, "Third definition")
            self.assert_code("service_busy", lambda: self.read(store))
        self.assertIsNone(store.retiring)
        third = self.read(store); self.assertNotEqual(second.snapshot_id, third.snapshot_id)
        with self.assertRaises(RuntimeError):
            with store.lease(): raise RuntimeError("Cancellation fixture")
        self.assertFalse(store._readers)
        with store.lease():
            with store.lease(): self.assert_code("service_busy", lambda: self.read(store))
        self.assertFalse(store._readers)

    def test_same_identity_other_root_isolated(self):
        a = self.read(self.store()); other = make_project(self.base / "other")
        b = self.read(self.store(other)); self.assertNotEqual(a.root_scope_id, b.root_scope_id); self.assertNotEqual(a.key, b.key)

    def test_replaced_root_requires_new_epoch_lifecycle(self):
        store = self.store(); self.read(store)
        self.root.rename(self.base / "old"); make_project(self.root)
        self.assert_code("package_changed", lambda: self.read(store)); self.assertTrue(store.package.changed)

    def test_byte_capture_never_loads_mid_read_replacement(self):
        target = self.authored(); store = self.store(); original = store._materialize; calls = []
        def replace(capture):
            calls.append(1)
            if len(calls) == 1: self.change_definition(target, "Replacement complete version")
            return original(capture)
        with patch.object(store, "_materialize", replace): result = self.read(store)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result.project.by_id[project_id("one")]["definition"], "Replacement complete version")

    def test_continuous_churn_stops_after_three_attempts(self):
        target = self.authored(); store = self.store(); original = store._materialize; calls = []
        def replace(capture):
            calls.append(1); self.change_definition(target, "Churn " + str(len(calls))); return original(capture)
        with patch.object(store, "_materialize", replace): self.assert_code("snapshot_changed", lambda: self.read(store))
        self.assertEqual(len(calls), 3); self.assertIsNone(store.current)

    def test_deadline_before_opaque_work(self):
        self.assert_code("deadline_exceeded", lambda: self.read(self.store(), deadline=time.monotonic()-1))

    def test_existing_exclusive_lock_is_busy_and_read_does_not_replace_it(self):
        store = self.store()
        with operation_lock(self.root, "control_records/ontology/publication.lock"):
            before = inventory(self.root); self.assert_code("knowledge_updating", lambda: self.read(store)); self.assertEqual(before, inventory(self.root))
        self.assertTrue(self.read(store))

    def test_shared_lock_blocks_actual_publisher_through_postcheck(self):
        bind_director(self.root); prop = proposal(self.root, [record("published")]); g = grant(self.root, prop)
        with operation_lock(self.root, "control_records/ontology/publication.lock"): pass
        store = self.store(); original = store._materialize; observations = []
        def attempt(capture):
            try: publish(self.root, prop, g, expected_preview_sha256=g["preview_sha256"])
            except ValueError as exc: observations.append(exc.code)
            return original(capture)
        with patch.object(store, "_materialize", attempt): view = self.read(store)
        self.assertEqual(observations, ["operation_locked"])
        self.assertNotIn(project_id("published"), view.project.by_id)

    def test_missing_lock_actual_completed_publication_retries(self):
        bind_director(self.root); prop = proposal(self.root, [record("published")]); g = grant(self.root, prop)
        store = self.store(); original = store._materialize; results = []
        def publish_between(capture):
            if not results: results.append(publish(self.root, prop, g, expected_preview_sha256=g["preview_sha256"])["status"])
            return original(capture)
        with patch.object(store, "_materialize", publish_between): view = self.read(store)
        self.assertEqual(results, ["complete"]); self.assertIn(project_id("published"), view.project.by_id)

    def test_missing_lock_barrier_with_active_actual_publisher(self):
        bind_director(self.root); prop = proposal(self.root, [record("published")]); g = grant(self.root, prop)
        store = self.store(); original = store._materialize; entered = threading.Event(); release = threading.Event(); outcome = []
        import ontology_publication
        advance = ontology_publication._advance
        def held_advance(*args, **kw):
            entered.set(); self.assertTrue(release.wait(4)); return advance(*args, **kw)
        def writer():
            try: outcome.append(publish(self.root, prop, g, expected_preview_sha256=g["preview_sha256"])["status"])
            except BaseException as exc: outcome.append(type(exc).__name__)
        thread = threading.Thread(target=writer)
        def between(capture):
            if not thread.is_alive() and not outcome: thread.start(); self.assertTrue(entered.wait(4))
            return original(capture)
        try:
            with patch.object(ontology_publication, "_advance", held_advance), patch.object(store, "_materialize", between):
                self.assert_code("knowledge_updating", lambda: self.read(store))
        finally:
            release.set(); thread.join(5)
        self.assertEqual(outcome, ["complete"]); self.assertIn(project_id("published"), self.read(store).project.by_id)

    def test_absent_parent_creation_retries_without_creating_lock(self):
        store = self.store(); original = store._materialize; calls = []
        def appear(capture):
            calls.append(1)
            if len(calls) == 1: (self.root / "control_records").mkdir()
            return original(capture)
        with patch.object(store, "_materialize", appear): self.read(store)
        self.assertEqual(len(calls), 2); self.assertFalse((self.root / "control_records/ontology/publication.lock").exists())

    def test_unsafe_coordination_is_bounded_refusal(self):
        (self.root / "control_records/ontology").mkdir(parents=True)
        outside = self.base / "outside"; outside.write_text("private string")
        lock = self.root / "control_records/ontology/publication.lock"; lock.symlink_to(outside)
        self.assert_code("knowledge_updating", lambda: self.read(self.store()))
        lock.unlink(); os.link(outside, lock)
        self.assert_code("knowledge_updating", lambda: self.read(self.store()))

    def test_module_file_set_addition_and_unknown_cached_input_rejected(self):
        store = self.store(); self.read(store)
        base = self.root / read_json(self.root / "ontology.yaml")["modules"][0]["path"]
        (base / "unexpected.txt").write_text("Unselected module addition")
        self.assert_code("canonical_invalid", lambda: self.read(store))

    def test_package_helper_schema_asset_and_set_drift_sticky(self):
        scripts = self.base / "scripts"; scripts.mkdir()
        for p in (PACKAGE / "scripts").glob("ontology*.py"): shutil.copyfile(p, scripts / p.name)
        schema = self.base / "schema.json"; shutil.copyfile(SCHEMA, schema)
        asset = self.base / "asset.js"; asset.write_text("export const fixture = 1;\n")
        for target in (scripts / "ontology_core.py", schema, asset, scripts / "ontology_new_fixture.py"):
            with self.subTest(target=target.name):
                store = self.store(scripts=scripts, schema_path=schema, package_files={"asset": asset}); self.read(store)
                before = target.read_bytes() if target.exists() else None
                st = target.stat() if before is not None else None
                target.write_bytes((before or b"") + b"\n")
                if st: os.utime(target, ns=(st.st_atime_ns, st.st_mtime_ns))
                exc = self.assert_code("package_changed", lambda: self.read(store)); self.assertIsInstance(exc, store.error_type)
                if before is None: target.unlink()
                else: target.write_bytes(before)
                self.assert_code("package_changed", lambda: self.read(store))
        self.assertTrue(self.read(self.store(scripts=scripts, schema_path=schema, package_files={"asset": asset})))

    def test_loaded_closure_rejects_ambient_core_and_never_reuses_bytecode(self):
        import ontology_core
        with patch.object(ontology_core, "load_project", side_effect=AssertionError("Ambient function must not run")):
            store = self.store(); self.assertEqual(len(self.read(store).project.records), 65)
        self.assertNotEqual(store.core.__name__, "ontology_core")
        self.assertEqual(store.package.loaded_digests["ontology_core"], sha256(PACKAGE / "scripts/ontology_core.py"))
        with self.assertRaises(ValueError): store.package.load("ontology_publication")

    def test_captured_helper_digest_checked_before_any_execution(self):
        import ontology_explorer_snapshot as snapshot
        original = snapshot._file; reads = []; marker = self.base / "unverified-executed"
        payload = ("\nfrom pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('bad')\n").encode()
        def swapped(path, maximum=2_000_000):
            raw = original(path, maximum)
            if Path(path).name == "ontology_core.py":
                reads.append(1)
                if len(reads) == 2: return raw + payload
            return raw
        with patch.object(snapshot, "_file", swapped):
            self.assert_code("package_incomplete", lambda: self.store())
        self.assertEqual(len(reads), 2); self.assertFalse(marker.exists())

    def test_stdlib_import_cannot_execute_ambient_path_or_custom_finder(self):
        ambient = self.base / "ambient"; ambient.mkdir(); marker = self.base / "ambient-executed"
        (ambient / "unicodedata.py").write_text("from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('bad')\n")
        previous = sys.modules.pop("unicodedata", None)
        class Finder:
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "unicodedata": raise AssertionError("Ambient finder reached")
                return None
        try:
            with patch.object(sys, "path", [str(ambient), *sys.path]), patch.object(sys, "meta_path", [Finder(), *sys.meta_path]):
                store = self.store(); self.assertTrue(self.read(store))
            self.assertFalse(marker.exists())
            self.assertIn("lib-dynload", str(sys.modules["unicodedata"].__spec__.origin))
        finally:
            if previous is not None: sys.modules["unicodedata"] = previous

    def test_preloaded_fake_stdlib_module_is_rejected(self):
        from types import ModuleType
        from importlib.machinery import ModuleSpec
        fake = ModuleType("unicodedata"); fake.__spec__ = ModuleSpec("unicodedata", None, origin=str(self.base / "unicodedata.py"))
        (self.base / "unicodedata.py").write_text("# ambient data\n")
        with patch.dict(sys.modules, {"unicodedata": fake}):
            self.assert_code("package_incomplete", lambda: self.store())

    def test_package_capture_enforces_budget_before_next_allocation(self):
        import ontology_explorer_snapshot as snapshot
        members = {}; observed = []; original = snapshot._file
        for n in range(5):
            f = self.base / ("member" + str(n)); f.write_bytes(b" " * (8 * 1024**2)); members[str(n)] = f
        def observed_file(path, maximum=2_000_000):
            if Path(path).name.startswith("member"): observed.append(maximum)
            return original(path, maximum)
        with patch.object(snapshot, "_file", observed_file):
            self.assert_code("package_incomplete", lambda: self.store(package_files=members))
        self.assertLess(observed[-1], 8 * 1024**2)
        self.assertLessEqual(len(observed), 4)

    def test_tightened_journal_and_deadline_policy_applies_first_request(self):
        bind_director(self.root); prop = proposal(self.root, [record("one")]); g = grant(self.root, prop)
        publish(self.root, prop, g, expected_preview_sha256=g["preview_sha256"])
        write_json(self.root / "ontology-explorer.yaml", {"schema_version": 1, "project_id": "example", "limits": {"journal_files": 1}})
        store = self.store(); module = sys.modules[type(store).__module__]; original = module._journals; seen = []
        def observe_journal(root, limits, deadline):
            seen.append(limits["journal_files"]); return original(root, limits, deadline)
        with patch.object(module, "_journals", observe_journal):
            self.assert_code("resource_limit", lambda: self.read(store))
        self.assertEqual(seen, [1])
        write_json(self.root / "ontology-explorer.yaml", {"schema_version": 1, "project_id": "example", "limits": {"request_seconds": 1}})
        store = self.store(); original_policy = store._policy
        def slow_policy():
            result = original_policy(); time.sleep(1.02); return result
        with patch.object(store, "_policy", slow_policy):
            self.assert_code("deadline_exceeded", lambda: self.read(store))

    def test_source_file_and_full_tuple_limits_are_independent(self):
        fixture = make_explorer_project(self.base / "scale", pathological=False)
        write_json(fixture["root"] / "ontology-explorer.yaml", {"schema_version": 1, "project_id": fixture["identity"], "limits": {"source_files": 10}})
        self.assertGreater(fixture["counts"]["owner_source_reference_tuples"], 10)
        self.assertLessEqual(fixture["counts"]["distinct_source_paths"], 10)
        self.assertTrue(self.read(self.store(fixture["root"])))
        limit = fixture["counts"]["distinct_source_paths"] - 1
        self.assert_code("resource_limit", lambda: self.read(self.store(fixture["root"], limits={"source_files": limit})))
        boundary = make_explorer_project(self.base / "references", entries=958, relationships=0, pathological=False)
        (boundary["root"] / "ontology-explorer.yaml").unlink()
        self.assertEqual(boundary["counts"]["owner_source_reference_tuples"], 1025)
        self.assert_code("resource_limit", lambda: self.read(self.store(boundary["root"])))

    def test_zero_relationships_is_valid_policy_but_refuses_nine_core_relations(self):
        store = self.store(limits={"relationships": 0})
        self.assert_code("resource_limit", lambda: self.read(store))
        write_json(self.root / "ontology-explorer.yaml", {"schema_version": 1, "project_id": "example", "limits": {"relationships": 0}})
        self.assert_code("resource_limit", lambda: self.read(self.store()))

    def test_selected_and_view_resources_are_bounded(self):
        self.assert_code("resource_limit", lambda: self.read(self.store(limits={"selected_files": 1})))
        cfg = read_json(self.root / "ontology.yaml"); (self.root / cfg["project_files"][0]).write_bytes(b" "*2_000_001)
        self.assert_code("resource_limit", lambda: self.read(self.store()))

    def test_ordinary_partial_stable_commit_and_retained_recovery(self):
        bind_director(self.root); prop = proposal(self.root, [record("published")]); g = grant(self.root, prop)
        partial = publish(self.root, prop, g, expected_preview_sha256=g["preview_sha256"], fail_at="after_commit")
        self.assertEqual(partial["status"], "partial"); store = self.store(); before = inventory(self.root)
        self.assert_code("knowledge_updating", lambda: self.read(store)); self.assertEqual(before, inventory(self.root))
        self.assertEqual(recover(self.root, prop["operation_id"], g)["status"], "complete")
        self.assertTrue((self.root / "control_records/ontology/recovery" / (prop["operation_id"]+".json")).exists())
        self.assertIn(project_id("published"), self.read(store).project.by_id)

    def test_all_target_bytes_without_receipt_remain_unresolved(self):
        bind_director(self.root); prop = proposal(self.root, [record("published")]); g = grant(self.root, prop)
        publish(self.root, prop, g, expected_preview_sha256=g["preview_sha256"], fail_at="receipt")
        (self.root / "control_records/ontology/recovery" / (prop["operation_id"]+".json")).unlink()
        self.assertEqual(sha256(self.root / prop["changes"][0]["path"]), prop["changes"][0]["sha256"])
        self.assert_code("knowledge_updating", lambda: self.read(self.store()))

    def test_complete_historical_receipt_accepts_later_superseding_publication(self):
        bind_director(self.root)
        first = proposal(self.root, [record("one")]); g = grant(self.root, first)
        self.assertEqual(publish(self.root, first, g, expected_preview_sha256=g["preview_sha256"])["status"], "complete")
        second = proposal(self.root, [record("one"), record("two")], operation_id="ONTOP-later-complete"); g2 = grant(self.root, second)
        self.assertEqual(publish(self.root, second, g2, expected_preview_sha256=g2["preview_sha256"])["status"], "complete")
        self.assertNotEqual(first["changes"][0]["sha256"], sha256(self.root / first["changes"][0]["path"]))
        self.assertIn(project_id("two"), self.read(self.store()).project.by_id)

    def test_malformed_orphan_and_mismatched_journals_fail_closed(self):
        bind_director(self.root); prop = proposal(self.root, [record("one")]); g = grant(self.root, prop)
        publish(self.root, prop, g, expected_preview_sha256=g["preview_sha256"])
        intent = self.root / "control_records/ontology/intents" / (prop["operation_id"]+".json")
        receipt = self.root / "control_records/ontology/receipts" / intent.name
        original = intent.read_bytes(); saved_receipt = receipt.read_bytes()
        for mutation in (lambda: intent.write_bytes(b'{"bad":'), lambda: intent.unlink(),
                         lambda: receipt.write_bytes(saved_receipt.replace(b'"committed"', b'"pending"'))):
            intent.write_bytes(original); receipt.write_bytes(saved_receipt); mutation()
            self.assert_code("knowledge_updating", lambda: self.read(self.store()))
        intent.write_bytes(original); receipt.write_bytes(saved_receipt)
        data = read_json(intent); path = prop["changes"][0]["path"]; data["prior_contents"][path] += " "
        data["intent_sha256"] = sha256(canonical_bytes({k:v for k,v in data.items() if k != "intent_sha256"})); write_json(intent, data)
        self.assert_code("knowledge_updating", lambda: self.read(self.store()))

    def test_disjoint_unresolved_actual_transaction_is_excluded(self):
        bind_director(self.root); prop = proposal(self.root, [record("one")]); g = grant(self.root, prop)
        publish(self.root, prop, g, expected_preview_sha256=g["preview_sha256"], fail_at="before_commit")
        # Explicit fixture setup unselects the historical target and selects a new
        # empty graph. The preserved intent is provably disjoint, not repaired.
        cfg = read_json(self.root / "ontology.yaml"); cfg["project_files"] = ["ONTOLOGY/modules/project/other.jsonld"]
        write_json(self.root / cfg["project_files"][0], {"@context": cfg["context"]["path"], "@graph": []}); write_json(self.root / "ontology.yaml", cfg)
        self.assertTrue(self.read(self.store()))

    def test_integration_partial_multifile_and_recovery_receipt_shapes(self):
        root = integration_fixture(self.base / "integration")
        pre = integration_preview(root, {"schema_version": 1, "operation_id": "ONTOP-snapshot-integration", "reason": "Snapshot observer test."}); g = integration_grant(root, pre)
        partial = integration_publish(root, pre["proposal"], g, expected_preview_sha256=pre["preview_sha256"], fail_at="after_commit:2")
        self.assertEqual(partial["status"], "partial"); store = self.store(root)
        before = inventory(root); self.assert_code("knowledge_updating", lambda: self.read(store)); self.assertEqual(before, inventory(root))
        final = integration_recover(root, pre["proposal"]["operation_id"], g); self.assertEqual(final["status"], "complete")
        self.assertTrue(all("state" not in row for row in final["files"]))
        self.assertGreater(len(self.read(store).project.records), 65)

    def test_journal_aggregate_bound_across_families(self):
        bind_director(self.root); prop = proposal(self.root, [record("one")]); g = grant(self.root, prop)
        publish(self.root, prop, g, expected_preview_sha256=g["preview_sha256"])
        self.assert_code("resource_limit", lambda: self.read(self.store(limits={"journal_files": 1})))


if __name__ == "__main__": unittest.main(verbosity=2)
