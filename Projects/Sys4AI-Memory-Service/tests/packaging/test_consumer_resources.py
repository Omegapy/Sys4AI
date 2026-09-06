from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
import zipfile
from importlib.resources import files
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from sys4ai_memory.authorization import CanonicalPermissionDocument
from sys4ai_memory.bootstrap import prepare_project_memory
from sys4ai_memory.configuration.models import MemoryConfiguration
from sys4ai_memory.contracts.schema import PUBLIC_CONTRACT_MODELS, public_contract_schema
from sys4ai_memory.profiles import ProfileDefinition
from sys4ai_memory.sources import load_registry_bundle


def test_packaged_schemas_match_current_runtime_contracts() -> None:
    resources = files("sys4ai_memory.package_data").joinpath("consumer_v1")
    for name in PUBLIC_CONTRACT_MODELS:
        schema = json.loads(resources.joinpath("schemas/memory", name).read_text())
        assert schema == public_contract_schema(name)
        Draft202012Validator.check_schema(schema)
    for name, model in (
        ("profile-definition", ProfileDefinition),
        ("memory-configuration", MemoryConfiguration),
        ("canonical-permissions", CanonicalPermissionDocument),
    ):
        schema = json.loads(resources.joinpath(f"schemas/memory/{name}.schema.json").read_text())
        assert schema == {
            **model.model_json_schema(),
            "$schema": "https://json-schema.org/draft/2020-12/schema",
        }
        Draft202012Validator.check_schema(schema)


def test_every_generated_schema_and_profile_reference_resolves_in_consumer(tmp_path: Path) -> None:
    prepare_project_memory(tmp_path, "isolated-project", "Isolated Project", "isolated-owner")
    registry = load_registry_bundle(
        project_root=tmp_path,
        source_registry=tmp_path / "registries/memory_source_registry.csv",
        profile_registry=tmp_path / "registries/memory_profile_registry.csv",
        relation_registry=tmp_path / "registries/memory_relation_registry.csv",
    )
    for profile in registry.profiles:
        schema = json.loads((tmp_path / profile.schema_ref).read_text())
        definition = yaml.safe_load((tmp_path / profile.config_ref).read_text())
        Draft202012Validator(schema).validate(definition)
        loaded = ProfileDefinition.model_validate(definition)
        for reference in (
            *(record.schema_ref for record in loaded.record_types),
            *(reference.ref for _, reference in loaded.behavior_references()),
            *(reference.ref for reference in loaded.evaluations),
        ):
            assert (tmp_path / reference).is_file(), reference
        assert (tmp_path / profile.write_policy_ref).is_file()
        if profile.migration_ref is not None:
            assert (tmp_path / profile.migration_ref).is_file()
    for relative, schema_name, parse in (
        ("config/memory.toml", "memory-configuration", tomllib.loads),
        ("control_records/memory/permissions.json", "canonical-permissions", json.loads),
    ):
        schema = json.loads((tmp_path / f"schemas/memory/{schema_name}.schema.json").read_text())
        Draft202012Validator(schema).validate(parse((tmp_path / relative).read_text()))
    assert not (tmp_path / ".sys4ai").exists()
    assert not (tmp_path / "src").exists()


def test_resources_have_no_real_identity_host_paths_or_initialized_state() -> None:
    resources = files("sys4ai_memory.package_data").joinpath("consumer_v1")
    manifest = json.loads(resources.joinpath("manifest.json").read_text())
    assert manifest["resource_version"] == "1.0.0"
    assert manifest["default_profile"] == "base@1"
    assert len(manifest["files"]) == len(set(manifest["files"]))
    for relative in manifest["files"]:
        assert not relative.startswith((".sys4ai/", ".venv/", "models/", ".git/"))
        content = resources.joinpath(relative).read_bytes()
        for forbidden in (b"/Users/", b"/Volumes/", b"sys4ai-memory-service", b"sys4ai-depot"):
            assert forbidden not in content, relative
    permissions = json.loads(
        resources.joinpath("control_records/memory/permissions.json").read_text()
    )
    assert permissions["approval_policy"] is None
    assert {grant["principal_id"] for grant in permissions["grants"]} == {"__PRINCIPAL_ID__"}
    assert all(not grant["shared_project_ids"] for grant in permissions["grants"])


def test_built_wheel_loads_consumer_without_editable_checkout(tmp_path: Path) -> None:
    selected = os.environ.get("SYS4AI_CONSUMER_WHEEL")
    if not selected:
        pytest.skip("Set SYS4AI_CONSUMER_WHEEL to exercise the separately built immutable wheel")
    wheel = Path(selected).resolve(strict=True)
    resources = files("sys4ai_memory.package_data").joinpath("consumer_v1")
    manifest = json.loads(resources.joinpath("manifest.json").read_text())
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        for relative in [*manifest["files"], "manifest.json", "ignore-rules.txt"]:
            assert f"sys4ai_memory/package_data/consumer_v1/{relative}" in names
        assert "sys4ai_memory/bootstrap/prepare.py" in names
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    script = r"""
import importlib.abc
import io
import json
import sys
from pathlib import Path

wheel, consumer = sys.argv[1:]
sys.path = [wheel, *(p for p in sys.path if not p.endswith('/src'))]

class DenyNativeProvider(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'cognee' or fullname.startswith('cognee.'):
            raise AssertionError('preparation imported a native provider')

sys.meta_path.insert(0, DenyNativeProvider())
from sys4ai_memory.bootstrap import prepare_project_memory
from sys4ai_memory.bootstrap.prepare import _validate_generated
from sys4ai_memory.cli import main

root = Path(consumer)
result = prepare_project_memory(root, 'wheel-consumer', 'Wheel Consumer', 'wheel-owner')
_validate_generated(root)
output = io.StringIO()
code = main(['--project-root', str(root), '--project-id', result.project_id,
             '--dataset-id', result.dataset_id, '--principal-id', result.principal_id,
             '--agent-type', 'fixture', '--run-id', 'wheel-check', 'health'], stdout=output)
assert code == 0, output.getvalue()
assert not (root / '.sys4ai').exists()
assert not (root / 'src').exists()
assert 'cognee' not in sys.modules
for name, module in sys.modules.items():
    if name == 'sys4ai_memory' or name.startswith('sys4ai_memory.'):
        assert module.__file__.startswith(wheel + '/'), (name, module.__file__)
print(json.dumps({'status': 'passed', 'resources': len(result.created_files),
                  'origin': 'wheel', 'provider_imported': False, 'storage_initialized': False}))
"""
    process = subprocess.run(  # noqa: S603 - current interpreter and disposable local fixture
        [sys.executable, "-I", "-c", script, str(wheel), str(consumer)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0"},
    )
    assert process.returncode == 0, process.stdout + process.stderr
    assert json.loads(process.stdout)["origin"] == "wheel"
