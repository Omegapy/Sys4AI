"""Explicit vendored imports; no ambient module discovery or network resolution."""
from pathlib import Path
import re
from ontology_core import (CORE, CONTEXT_PATH, TRUSTED_CONTEXT, canonical_bytes, sha256, read_json,
                           read_bytes, safe_path, relative_path, digest, require, exact, parse_document)


def module_digest(files):
    return sha256(canonical_bytes(files))


def load_modules(root, config):
    require(1 <= len(config["modules"]) <= 8, "invalid_modules", "Select one to eight locked local modules.")
    records, modules, locations, inputs, seen_modules = [], [], {}, {}, set()
    for lock in config["modules"]:
        exact(lock, ("id", "version", "path", "sha256"))
        require(lock["id"] == "sys4ai-core" and lock["id"] not in seen_modules, "unsupported_module", "The first release imports one locked sys4ai-core; domain extensions remain project-local.")
        seen_modules.add(lock["id"])
        require(isinstance(lock["version"], str) and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", lock["version"]), "module_version", "Module version must be explicit.")
        require(lock["path"] == f"ONTOLOGY/modules/{lock['id']}/{lock['version']}", "module_path", "Selected module path must include its exact identity and version.")
        digest(lock["sha256"])
        base = safe_path(root, lock["path"])
        manifest_path = lock["path"] + "/manifest.json"
        manifest = read_json(safe_path(root, manifest_path))
        exact(manifest, ("schema_version", "module_id", "version", "files", "record_files"))
        require(type(manifest["schema_version"]) is int and manifest["schema_version"] == 1 and manifest["module_id"] == lock["id"] and manifest["version"] == lock["version"], "module_version", "Manifest identity/version differs from selected import.", path=manifest_path)
        files = manifest["files"]
        require(isinstance(files, dict) and files and len(files) <= 100, "module_manifest", "Expected bounded manifest file hashes.")
        require(module_digest(files) == lock["sha256"], "module_digest", "Module file-set digest differs from the import lock.", path=manifest_path)
        actual_names = set()
        for p in base.rglob("*"):
            require(not p.is_symlink(), "unsafe_symlink", "Module contains a symlink.", path=p.relative_to(root).as_posix())
            if p.is_file(): actual_names.add(p.relative_to(base).as_posix())
        require(actual_names == set(files) | {"manifest.json"}, "module_file_set", "Module file set differs from its complete manifest.", path=lock["path"])
        for name, expected in sorted(files.items()):
            relative_path(name); digest(expected)
            require(name != "manifest.json", "module_manifest", "Manifest cannot hash itself.")
            relative = lock["path"] + "/" + name
            actual = sha256(safe_path(root, relative))
            require(actual == expected, "module_integrity", "Vendored module file differs from its locked version.", path=relative)
            inputs[relative] = actual
        require("context-v1.jsonld" in files and files["context-v1.jsonld"] == config["context"]["sha256"] and read_json(base / "context-v1.jsonld") == TRUSTED_CONTEXT, "module_context", "Module must manifest the identical trusted context.")
        require(isinstance(manifest["record_files"], list) and manifest["record_files"] and all(isinstance(p, str) for p in manifest["record_files"]) and len(manifest["record_files"]) == len(set(manifest["record_files"])) and all(p in files and p.endswith(".jsonld") and p != "context-v1.jsonld" for p in manifest["record_files"]), "module_manifest", "Record files must be selected uniquely in the manifest.")
        for name in sorted(manifest["record_files"]):
            relative = lock["path"] + "/" + name
            for record, location in parse_document(read_bytes(safe_path(root, relative)), CONTEXT_PATH, relative):
                require(record["@id"].startswith(CORE) and record.get("module") == lock["id"], "module_ownership", "Imported records must retain shared core identity and ownership.", path=location, record_id=record["@id"])
                require(record["@id"] not in locations, "duplicate_id", "Duplicate imported identity.", path=location, record_id=record["@id"])
                require(record["kind"] in {"concept", "predicate", "relation"}, "core_instance", "Reusable modules cannot contain project instances or bindings.", path=location)
                records.append(record); locations[record["@id"]] = location
        manifest_hash = sha256(base / "manifest.json")
        inputs[manifest_path] = manifest_hash
        modules.append({**lock, "manifest_sha256": manifest_hash, "files": files})
    return records, modules, locations, inputs
