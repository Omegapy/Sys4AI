"""Completion capture and explicit user preference changes; no background worker."""
from __future__ import annotations

from memory_core import load_config, json_bytes, sha256, validate_config
from memory_paths import require, safe_read_bytes

TRIGGERS = ("work-completed", "task-completed", "decision-recorded", "failure-observed")


def capture_status(root):
    config = load_config(root)
    enabled = config["integration"]["automatic_capture"]
    return {"automatic_capture": enabled, "triggers": list(TRIGGERS),
            "config_sha256": sha256(safe_read_bytes(root, "memory.yaml")),
            "read_only": True,
            "message": "Memory automatic capture is " + ("on." if enabled else "off.")}


def set_capture(root, enabled, expected_config_sha256):
    """Called only for an explicit user setting change; preserve every other field."""
    from memory_recovery import project_lock, atomic_replace, pending_transactions
    require(type(enabled) is bool, "invalid_setting", "Automatic capture must be a boolean.")
    raw = safe_read_bytes(root, "memory.yaml")
    require(sha256(raw) == expected_config_sha256, "config_conflict", "Memory configuration changed; inspect it again.")
    config = load_config(root)
    if config["integration"]["automatic_capture"] == enabled:
        return {**capture_status(root), "read_only": False, "mutated": False}
    with project_lock(root):
        require(not pending_transactions(root), "recovery_pending", "Resolve pending memory publication before changing configuration.")
        from memory_maintenance import pending_reindexes
        require(not pending_reindexes(root, config), "recovery_pending", "Resolve pending index maintenance before changing configuration.")
        config["integration"]["automatic_capture"] = enabled
        validate_config(config)
        atomic_replace(root, "memory.yaml", json_bytes(config), expected_config_sha256)
    return {**capture_status(root), "read_only": False, "mutated": True,
            "index_refresh_required": config["backend"]["enabled"]}


def capture(root, payload, grant_file, actor, *, trigger):
    """Publish a reviewed checkpoint finding when enabled, using existing authority.

    The Director supplies evidence and judgment. This helper does not invent
    findings, authorize itself, or turn a Task transition into a memory write.
    Existing transaction IDs make a repeated completion call idempotent.
    """
    require(trigger in TRIGGERS, "invalid_trigger", "Unsupported automatic capture checkpoint.")
    if not load_config(root)["integration"]["automatic_capture"]:
        return {"status": "skipped", "reason": "automatic_capture_off", "mutated": False, "trigger": trigger}
    require(payload.get("operation") in {"publish", "supersede"}, "invalid_capture", "Capture publishes a finding or its reviewed successor.")
    from memory_publish import publish
    result = publish(root, payload, grant_file, actor)
    return {"status": "captured", "trigger": trigger, "publication": result}


# Optional action guard adapter.  Standalone/core use imports no ontology runtime.
def _ontology_checkpoint(*, targets=True):
    import sys as _sys
    _module = _sys.modules.get("ontology_guards")
    if _module is not None:
        _module.checkpoint(targets=targets)


def _ontology_guard_adapter(function, family, root_argument, target_paths):
    import functools as _functools
    import inspect as _inspect
    @_functools.wraps(function)
    def guarded(*args, **kwargs):
        import importlib.util as _util
        import sys as _sys
        from pathlib import Path as _Path
        arguments = dict(_inspect.signature(function).bind(*args, **kwargs).arguments)
        if root_argument == "@depot":
            selected_root = installed_locations()[0]
        else:
            selected_root = arguments[root_argument]
            if not isinstance(selected_root, (_Path, str)):
                selected_root = getattr(selected_root, "project_root", getattr(selected_root, "root", selected_root))
        selected_root = _Path(selected_root).absolute()
        config_path = selected_root / "ontology-advanced.yaml"
        if not config_path.exists() and not config_path.is_symlink():
            return function(*args, **kwargs)
        if family == "template" and arguments.get("command") == "check":
            return function(*args, **kwargs)
        import json as _json
        import hashlib as _hashlib
        def unique_pairs(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError("duplicate guard configuration key")
                value[key] = item
            return value
        try:
            if config_path.is_symlink():
                raise ValueError("symbolic guard configuration")
            config = _json.loads(config_path.read_text(), object_pairs_hook=unique_pairs)
            selected = config.get("profiles", {}).get("guards", {"enabled": False})
            if config.get("schema_version") != 1 or not isinstance(selected, dict) or type(selected.get("enabled")) is not bool:
                raise ValueError("unsupported guard configuration")
        except (OSError, ValueError, AttributeError) as exc:
            raise _ontology_adapter_error("guard_schema", "Guard configuration is unreadable or unsupported.", {}) from exc
        if not selected["enabled"]:
            if set(selected) != {"enabled"}:
                raise _ontology_adapter_error("guard_schema", "Disabled guard configuration has unsupported fields.", {})
            return function(*args, **kwargs)
        script = selected_root / ".agents/skills/ontology/scripts/ontology_guards.py"
        if not script.is_file() or any(parent.is_symlink() for parent in (script, *script.parents)):
            raise _ontology_adapter_error("guard_unavailable", "Enabled guards require their current project-local installed adapter.", {})
        current_sha256 = _hashlib.sha256(script.read_bytes()).hexdigest()
        module = _sys.modules.get("ontology_guards")
        if module is not None and (_Path(module.__file__).resolve() != script.resolve()
                or getattr(module, "ENGINE_SOURCE_SHA256", None) != current_sha256):
            raise _ontology_adapter_error("guard_stale", "Loaded guard code differs from this selected project's current installed bytes; use a fresh owning-helper process after reviewed repair.", {})
        if module is None:
            spec = _util.spec_from_file_location("ontology_guards", script)
            module = _util.module_from_spec(spec)
            _sys.modules["ontology_guards"] = module
            _sys.path.insert(0, str(script.parent))
            spec.loader.exec_module(module)
        targets = list(target_paths)
        if family == "setup":
            destination = _Path(arguments["destination"]).absolute()
            try:
                relative = destination.relative_to(selected_root).as_posix()
            except ValueError:
                raise _ontology_adapter_error("guard_scope", "Setup target escapes the selected depot.", {})
            targets.extend([relative + "/control_records/project-setup.json", relative + "/AGENTS.md", relative + "/ROLE.md"])
        try:
            return module.dispatch(lambda: function(*args, **kwargs), family, function.__name__, selected_root, arguments, targets)
        except module.GuardError as exc:
            raise _ontology_adapter_error(exc.code, str(exc), exc.details) from exc
    return guarded


def _ontology_adapter_error(code, message, details):
    return __import__("memory_paths").MemoryError(code, message, details)

ONTOLOGY_GUARDED_ACTIONS = ['set_capture', 'capture']
set_capture = _ontology_guard_adapter(set_capture, 'memory', 'root', ['memory.yaml'])
capture = _ontology_guard_adapter(capture, 'memory', 'root', ['memory.yaml'])
