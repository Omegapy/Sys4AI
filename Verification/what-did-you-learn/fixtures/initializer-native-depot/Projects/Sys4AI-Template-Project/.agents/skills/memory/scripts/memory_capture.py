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
