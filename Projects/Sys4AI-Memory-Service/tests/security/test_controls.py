from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sys4ai_memory.contracts import AuthorityTier, TrustClass
from sys4ai_memory.security import (
    AuditEvent,
    AuthorityEscalationError,
    DatasetIsolationMap,
    DeploymentMode,
    DeploymentSecurityPosture,
    InMemoryAuditSink,
    JsonlAuditSink,
    PolicyDisabledError,
    ProjectBoundary,
    ProjectIsolationError,
    SecretDetectedError,
    UnsafePathError,
    bind_derived_authority,
    classify_external_content,
    redact_text,
    require_explicit_query_scope,
    require_no_authority_elevation,
    require_secret_free,
    require_shared_security,
    scan_text,
)
from sys4ai_memory.security.locks import exclusive_file_lock

FIXTURES = Path(__file__).parents[1] / "fixtures" / "security"


def test_prompt_injection_fixture_remains_untrusted_evidence() -> None:
    content = (FIXTURES / "prompt_injection_untrusted.md").read_text(encoding="utf-8")

    classified = classify_external_content(content)

    assert classified.instruction_like
    assert classified.authority_tier is AuthorityTier.UNTRUSTED_CONTENT
    assert classified.trust_class is TrustClass.UNTRUSTED
    assert classified.namespace == "evidence/external"
    assert not classified.may_enter_governance
    assert not classified.may_authorize_action
    assert classified.content == content


def test_summary_laundering_cannot_raise_source_authority() -> None:
    fixture = json.loads((FIXTURES / "summary_laundering.json").read_text(encoding="utf-8"))
    source = fixture["source"]

    binding = bind_derived_authority(
        AuthorityTier(source["authority_tier"]),
        TrustClass(source["trust_class"]),
        model_generated=False,
    )

    assert binding.effective_tier is AuthorityTier.UNTRUSTED_CONTENT
    assert binding.derived_trust is TrustClass.AGENT_GENERATED
    assert not binding.canonical
    assert not binding.may_authorize_action
    with pytest.raises(AuthorityEscalationError):
        require_no_authority_elevation(
            binding.source_tier,
            AuthorityTier.SYS4AI_GOVERNANCE,
            candidate_canonical=True,
        )


@pytest.mark.parametrize(
    "secret_text",
    [
        "api_key=" + "runtime" + "-only-value",
        "Bearer " + "runtime.generated.token.value",
        "sk-" + "runtimegenerated123456",
        "postgresql://user:" + "runtime-password" + "@localhost/db",
        "-----BEGIN " + "PRIVATE KEY-----",
    ],
)
def test_runtime_generated_secret_patterns_are_detected_without_echo(
    secret_text: str,
) -> None:
    findings = scan_text(secret_text)
    assert findings
    assert all(secret_text not in repr(finding) for finding in findings)
    with pytest.raises(SecretDetectedError) as captured:
        require_secret_free({"message": secret_text})
    assert secret_text not in str(captured.value)
    assert secret_text not in redact_text(secret_text)


def test_project_paths_and_dataset_mapping_are_isolated(tmp_path: Path) -> None:
    root = (tmp_path / "project").resolve()
    root.mkdir()
    (root / "docs").mkdir()
    source = root / "docs" / "source.md"
    source.write_text("content", encoding="utf-8")
    boundary = ProjectBoundary("project-a", "dataset-a", root)

    assert boundary.resolve_path("docs/source.md") == source
    for unsafe in ("../outside", "/absolute"):
        with pytest.raises(UnsafePathError):
            boundary.resolve_path(unsafe, must_exist=False)
    link = root / "linked"
    link.symlink_to(tmp_path)
    with pytest.raises(UnsafePathError):
        boundary.resolve_path("linked/file", must_exist=False)
    with pytest.raises(ProjectIsolationError):
        boundary.require_identity(project_id="project-b", dataset_id="dataset-a")

    mapping = DatasetIsolationMap({"project-a": "dataset-a", "project-b": "dataset-b"})
    mapping.require_pair("project-a", "dataset-a")
    with pytest.raises(ProjectIsolationError):
        mapping.require_pair("project-a", "dataset-b")
    with pytest.raises(ProjectIsolationError):
        DatasetIsolationMap({"project-a": "shared", "project-b": "shared"})


def test_advisory_lock_rejects_symlinks_and_hard_links(tmp_path: Path) -> None:
    target = tmp_path / "target.lock"
    target.write_text("", encoding="utf-8")
    symbolic = tmp_path / "symbolic.lock"
    symbolic.symlink_to(target)
    with pytest.raises(OSError), exclusive_file_lock(symbolic):
        raise AssertionError("symlink lock unexpectedly opened")

    hard_link = tmp_path / "hard.lock"
    hard_link.hardlink_to(target)
    with pytest.raises(OSError, match="regular non-linked"), exclusive_file_lock(hard_link):
        raise AssertionError("hard-linked lock unexpectedly opened")


def test_cross_project_and_shared_modes_fail_closed_without_all_gates() -> None:
    with pytest.raises(ProjectIsolationError):
        require_explicit_query_scope(
            service_project_id="project-a",
            requested_project_ids=("project-a", "project-b"),
            authorized_project_ids=frozenset({"project-a", "project-b"}),
            explicit_cross_project=False,
        )
    require_explicit_query_scope(
        service_project_id="project-a",
        requested_project_ids=("project-a", "project-b"),
        authorized_project_ids=frozenset({"project-a", "project-b"}),
        explicit_cross_project=True,
    )
    with pytest.raises(PolicyDisabledError):
        require_shared_security(
            shared_enabled=True,
            authenticated=False,
            backend_access_control=True,
            dataset_isolation=True,
        )
    require_shared_security(
        shared_enabled=True,
        authenticated=True,
        backend_access_control=True,
        dataset_isolation=True,
    )
    local = DeploymentSecurityPosture(
        mode=DeploymentMode.SINGLE_USER_DEVELOPMENT,
        authenticated=False,
        backend_access_control=False,
        dataset_isolation=True,
    )
    local.validate()
    assert "not a secure shared configuration" in local.security_label
    shared = DeploymentSecurityPosture(
        mode=DeploymentMode.SHARED,
        authenticated=True,
        backend_access_control=True,
        dataset_isolation=True,
    )
    shared.validate()
    assert shared.security_label == "authenticated shared deployment"


def _event() -> AuditEvent:
    return AuditEvent(
        event_id="event-1",
        occurred_at=datetime(2026, 9, 3, 12, 0, tzinfo=UTC),
        principal_id="agent-a",
        project_id="project-a",
        dataset_id="dataset-a",
        operation="memory.propose",
        target_ids=("mwp-proposal",),
        policy_decision="stage_for_review",
        outcome="staged",
        trace_id="trace-audit",
        policy_id="memory-write-policy@1",
        permission_revision="perm-1",
        counts=(("proposals", 1),),
    )


def test_audit_events_capture_principal_and_policy_without_content(tmp_path: Path) -> None:
    memory_sink = InMemoryAuditSink()
    event = _event()
    memory_sink.record(event)
    assert memory_sink.events() == (event,)

    boundary = ProjectBoundary("project-a", "dataset-a", tmp_path.resolve())
    with pytest.raises(PolicyDisabledError):
        JsonlAuditSink(boundary, "derived/audit.jsonl", retention_policy_id=None)

    sink = JsonlAuditSink(
        boundary,
        "derived/audit.jsonl",
        retention_policy_id="operator-bounded-retention@1",
    )
    sink.record(event)
    payload = json.loads((tmp_path / "derived" / "audit.jsonl").read_text(encoding="utf-8"))
    assert payload["principal_id"] == "agent-a"
    assert payload["policy_decision"] == "stage_for_review"
    assert "content" not in payload


def test_audit_event_rejects_secret_like_metadata() -> None:
    secret = "Bearer " + "runtime.generated.token.value"
    with pytest.raises(SecretDetectedError):
        AuditEvent(
            event_id="event-unsafe",
            occurred_at=datetime(2026, 9, 3, 12, 0, tzinfo=UTC),
            principal_id=secret,
            project_id="project-a",
            dataset_id="dataset-a",
            operation="memory.propose",
            target_ids=(),
            policy_decision="reject",
            outcome="rejected",
            trace_id="trace-audit",
            policy_id="memory-write-policy@1",
            permission_revision=None,
        )
