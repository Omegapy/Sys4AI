#!/usr/bin/env python3
"""Read-only resolution of learning resources and declared memory interfaces."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

sys.dont_write_bytecode = True
MODULE_ID = "what-did-you-learn"
VERSION = "1.0.0"
CHECKPOINT = "references/automatic-capture.md"
MARKER = "<!-- sys4ai:learning-review-v1 -->"
TRIGGERS = ["work-completed", "task-completed", "decision-recorded", "failure-observed"]
# The supported 1.0.0 interface requires these complete package resources.
# A customized manifest cannot weaken completeness while retaining its version.
MEMORY_RESOURCES = {
    "SKILL.md", "README.md", "agents/openai.yaml", "requirements-extraction.txt", "requirements-backend-pilot.txt",
    *["scripts/" + name + ".py" for name in (
        "memory", "memory_capture", "memory_core", "memory_evidence", "memory_maintenance",
        "memory_normalization", "memory_normalize_html", "memory_normalize_pdf", "memory_normalize_tex",
        "memory_packet", "memory_paths", "memory_publish", "memory_recovery", "memory_search",
        "basic_memory_adapter", "basic_memory_projection")],
    *["references/" + name + ".md" for name in (
        "automatic-capture", "task-integration", "evidence-and-lifecycle", "publication-examples",
        "operations", "state-paths", "basic-memory-pilot")],
}
MEMORY_CONTRACTS = {"README.md", "policy.md", "publication-and-recovery.md", "schema/record-v1.json", "schema/config-v1.json"}


class ContractError(ValueError):
    def __init__(self, code, path, message):
        super().__init__(message)
        self.diagnostic = {"code": code, "path": str(path), "message": message}


def _read(root, relative):
    """Reject aliases and unsafe resources before reading; never execute content."""
    if not isinstance(relative, str) or not relative or "\\" in relative or any(
        part in {"", ".", ".."} for part in relative.split("/")
    ):
        raise ContractError("unsafe_resource", relative, "Expected an exact project-relative file path.")
    current = root
    parts = relative.split("/")
    for index, part in enumerate(parts):
        if part not in os.listdir(current):
            raise ContractError("missing_resource", relative, "Required resource is absent with this exact spelling.")
        current = current / part
        mode = current.lstat()
        if stat.S_ISLNK(mode.st_mode):
            raise ContractError("unsafe_resource", relative, "Linked resources are not supported.")
        if index < len(parts) - 1:
            if not stat.S_ISDIR(mode.st_mode):
                raise ContractError("unsafe_resource", relative, "Resource parent is not a directory.")
        elif not stat.S_ISREG(mode.st_mode) or mode.st_nlink != 1 or mode.st_size > 2_000_000:
            raise ContractError("unsafe_resource", relative, "Expected a bounded regular file without hard links.")
    return current.read_bytes()


def _json(raw, path):
    def distinct(pairs):
        data = {}
        for key, value in pairs:
            if key in data:
                raise ValueError("duplicate field")
            data[key] = value
        return data
    try:
        value = json.loads(raw, object_pairs_hook=distinct,
                           parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite value")))
        if not isinstance(value, dict):
            raise ValueError("object required")
        return value
    except (ValueError, UnicodeError) as exc:
        raise ContractError("invalid_contract", path, "Expected a valid JSON object without duplicate fields.") from exc


def _validate_manifest(data, path):
    expected = {"schema_version", "module_id", "module_version", "required_resources", "skill", "memory"}
    skill, memory = data.get("skill", {}), data.get("memory", {})
    valid = (set(data) == expected and type(data.get("schema_version")) is int and data["schema_version"] == 1
             and data.get("module_id") == MODULE_ID and data.get("module_version") == VERSION
             and isinstance(skill, dict) and set(skill) == {"name", "version", "required_resources"}
             and skill.get("name") == MODULE_ID and skill.get("version") == VERSION
             and isinstance(memory, dict) and set(memory) == {
                 "record_schema_version", "config_schema_version", "required_resources", "contract_resources",
                 "helper_commands", "capture_triggers", "shared_checkpoint", "checkpoint_contract"})
    if not valid:
        raise ContractError("incompatible_contract", path, "Learning module/skill manifest is not supported version 1.0.0.")
    if (any(type(memory[key]) is not int or memory[key] != 1 for key in ("record_schema_version", "config_schema_version"))
            or memory["capture_triggers"] != TRIGGERS or memory["shared_checkpoint"] != CHECKPOINT
            or memory["checkpoint_contract"] != "learning-review-v1"):
        raise ContractError("incompatible_contract", path, "Memory schema, capture trigger or shared-checkpoint contract is incompatible.")
    lists = [data["required_resources"], skill["required_resources"], memory["required_resources"],
             memory["contract_resources"], memory["helper_commands"]]
    if any(not isinstance(items, list) or not items or any(not isinstance(item, str) or not item for item in items)
           or len(items) != len(set(items)) for items in lists):
        raise ContractError("invalid_contract", path, "Expected distinct nonempty resource and command lists.")
    minimums = [(data["required_resources"], {"contract.json", "README.md", "policy.md", "review-contract.md", "assets/lesson-body-template.md"}),
                (skill["required_resources"], {"SKILL.md", "README.md", "agents/openai.yaml", "scripts/learning_contract.py", "references/module-resolution.md", "references/improvement-and-reuse.md"}),
                (memory["required_resources"], MEMORY_RESOURCES),
                (memory["contract_resources"], MEMORY_CONTRACTS),
                (memory["helper_commands"], {"health", "search", "read", "validate", "propose", "capture-status", "capture", "publish", "supersede", "retract", "recover"})]
    for items, required in minimums:
        missing = required - set(items)
        if missing:
            raise ContractError("incompatible_contract", path, "Manifest omits required interface resources or commands: " + ", ".join(sorted(missing)))


def _commands(raw):
    """Read literal argparse declarations, including its literal operation loop."""
    result = set()
    class Commands(ast.NodeVisitor):
        def __init__(self):
            self.bindings = {}

        def visit_For(self, node):
            try:
                values = ast.literal_eval(node.iter)
            except (ValueError, TypeError):
                values = None
            if isinstance(node.target, ast.Name) and isinstance(values, (list, tuple, set)):
                previous = self.bindings.copy()
                for value in values:
                    self.bindings[node.target.id] = value
                    for child in node.body:
                        self.visit(child)
                self.bindings = previous
            else:
                self.generic_visit(node)

        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "add_parser" and node.args:
                value = node.args[0]
                value = value.value if isinstance(value, ast.Constant) else self.bindings.get(value.id) if isinstance(value, ast.Name) else None
                if isinstance(value, str):
                    result.add(value)
            self.generic_visit(node)
    Commands().visit(ast.parse(raw))
    return sorted(result)


def _triggers(raw):
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "TRIGGERS" for target in node.targets):
            values = ast.literal_eval(node.value)
            return list(values) if isinstance(values, (list, tuple)) else []
    return []


def resolve(project_root: Path, skill_dir: Path | None = None):
    """Inspect one exact installed or explicitly selected source layout only."""
    root = Path(project_root)
    result = {"read_only": True, "layout": None,
              "module": {"id": MODULE_ID, "version": VERSION, "root": None, "contract_sha256": None, "compatible": False},
              "required_resources": [], "missing_resources": [], "incompatible_resources": [],
              "memory": {"required_resources": [], "missing_resources": [], "incompatible_resources": [],
                         "helper_commands": [], "capture_triggers": [], "interface_compatible": False, "checkpoint_compatible": False},
              "governance": {"completion_routing": False, "diagnostics": [], "route_paths": []}, "errors": [],
              "capabilities": {"manual_review": False, "shared_automatic_checkpoint": False,
                               "authorized_publication": "not_assessed", "optional_backend": "not_assessed"}}

    def problem(error, bucket):
        diagnostic = error.diagnostic
        result["errors"].append(diagnostic)
        bucket["missing_resources" if diagnostic["code"] == "missing_resource" else "incompatible_resources"].append(diagnostic["path"])

    def read(relative, bucket):
        try:
            return _read(root, relative)
        except ContractError as exc:
            problem(exc, bucket)
        except OSError:
            problem(ContractError("unreadable_resource", relative, "Resource could not be inspected."), bucket)
        return None

    try:
        if not root.is_absolute() or root != root.resolve(strict=True) or not root.is_dir():
            raise ContractError("project_root", root, "Supply the explicit real absolute project root.")
        installed = root / ".agents/skills" / MODULE_ID
        selected = installed if skill_dir is None else Path(skill_dir)
        if not selected.is_absolute():
            selected = root / selected
        source = root / "SKILLS-depo" / MODULE_ID
        if selected not in (installed, source):
            raise ContractError("skill_layout", selected, "Select this project's exact installed or reusable-source skill path.")
        result["layout"] = "source" if selected == source else "installed"
        module_rel = "LEARNING-depo" if selected == source else "reference-assets/LEARNING-depo"
        memory_rel = "SKILLS-depo/memory" if selected == source else ".agents/skills/memory"
        contracts_rel = "MEMORY-depo" if selected == source else "reference-assets/MEMORY-depo"
        skill_rel = selected.relative_to(root).as_posix()
        result["module"]["root"] = str(root / module_rel)
        result["memory"]["root"] = str(root / memory_rel)
        manifest_path = module_rel + "/contract.json"
        raw = read(manifest_path, result)
        if raw is None:
            return result
        manifest = _json(raw, manifest_path)
        result["module"]["contract_sha256"] = hashlib.sha256(raw).hexdigest()
        _validate_manifest(manifest, manifest_path)
        result["required_resources"] = [module_rel + "/" + p for p in manifest["required_resources"]] + [skill_rel + "/" + p for p in manifest["skill"]["required_resources"]]
        contents = {p: read(p, result) for p in result["required_resources"]}
        entry = contents.get(skill_rel + "/SKILL.md")
        if entry is not None and not (re.search(rb"(?m)^name: what-did-you-learn$", entry) and re.search(rb'(?m)^  version: "1\.0\.0"$', entry)):
            problem(ContractError("incompatible_skill", skill_rel + "/SKILL.md", "Learning skill must declare the matching name and version."), result)
        result["module"]["compatible"] = not (result["missing_resources"] or result["incompatible_resources"])

        memory = result["memory"]
        memory["required_resources"] = [memory_rel + "/" + p for p in manifest["memory"]["required_resources"]] + [contracts_rel + "/" + p for p in manifest["memory"]["contract_resources"]]
        contents = {p: read(p, memory) for p in memory["required_resources"]}
        for relative, content in contents.items():
            if relative.endswith(".py") and content is not None:
                try:
                    ast.parse(content)
                except (SyntaxError, ValueError, UnicodeError):
                    problem(ContractError("incompatible_syntax", relative, "Required memory Python resource has invalid syntax."), memory)
        for relative, inspect, key in ((memory_rel + "/scripts/memory.py", _commands, "helper_commands"),
                                      (memory_rel + "/scripts/memory_capture.py", _triggers, "capture_triggers")):
            if contents.get(relative) is not None:
                try:
                    memory[key] = inspect(contents[relative])
                    expected = manifest["memory"][key]
                    if (key == "capture_triggers" and memory[key] != expected) or (key == "helper_commands" and not set(expected).issubset(memory[key])):
                        raise ValueError("interface declaration mismatch")
                except (ValueError, SyntaxError, TypeError, UnicodeError):
                    problem(ContractError("incompatible_interface", relative, "Required memory command or trigger declarations are absent or incompatible."), memory)
        for kind in ("record", "config"):
            relative = contracts_rel + "/schema/" + kind + "-v1.json"
            if contents.get(relative) is not None:
                try:
                    schema = _json(contents[relative], relative)
                    properties = schema.get("properties")
                    version = properties.get("schema_version") if isinstance(properties, dict) else None
                    if not isinstance(version, dict) or type(version.get("const")) is not int or version["const"] != 1:
                        raise ContractError("incompatible_schema", relative, "Memory schema version must remain 1.")
                except ContractError as exc:
                    problem(exc, memory)
        memory["interface_compatible"] = not (memory["missing_resources"] or memory["incompatible_resources"])
        checkpoint = contents.get(memory_rel + "/" + CHECKPOINT)
        memory["checkpoint_compatible"] = bool(memory["interface_compatible"] and checkpoint and MARKER.encode() in checkpoint)
        if checkpoint is not None and not memory["checkpoint_compatible"]:
            result["errors"].append({"code": "shared_checkpoint_unavailable", "path": memory_rel + "/" + CHECKPOINT,
                                     "message": "Shared learning checkpoint is unavailable; preserve the memory-only workflow."})
        governance = result["governance"]
        for relative in ("SOUL.md", "AGENTS.md", "ROLE.md"):
            try:
                governing = _read(root, relative)
                if b".agents/skills/memory/references/automatic-capture.md" in governing:
                    governance["route_paths"].append(relative)
            except (ContractError, OSError) as exc:
                diagnostic = exc.diagnostic if isinstance(exc, ContractError) else {"code": "unreadable_resource", "path": relative, "message": "Governing file could not be inspected."}
                governance["diagnostics"].append(diagnostic)
        governance["completion_routing"] = bool(governance["route_paths"] and not governance["diagnostics"])
        if not governance["route_paths"]:
            governance["diagnostics"].append({"code": "completion_route_absent", "path": "SOUL.md, AGENTS.md, ROLE.md",
                                               "message": "No direct stable memory completion reference was found in current governing files."})
        result["errors"].extend(governance["diagnostics"])
        result["capabilities"]["manual_review"] = result["module"]["compatible"] and memory["interface_compatible"]
        result["capabilities"]["shared_automatic_checkpoint"] = bool(result["capabilities"]["manual_review"] and memory["checkpoint_compatible"] and governance["completion_routing"])
    except (ContractError, OSError) as exc:
        problem(exc if isinstance(exc, ContractError) else ContractError("project_root", root, "Project root could not be inspected."), result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--skill-dir")
    args = parser.parse_args(argv)
    result = resolve(Path(args.project_root), Path(args.skill_dir) if args.skill_dir else None)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["capabilities"]["shared_automatic_checkpoint"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
