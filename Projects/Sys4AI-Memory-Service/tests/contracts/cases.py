"""Representative public-contract payloads used by schema and model tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SHA_A = "a" * 64
SHA_B = "b" * 64


MEMORY_RECORD: dict[str, Any] = {
    "schema_version": "1.0",
    "api_version": "1.0",
    "record_id": "mem_01JTESTDECISION",
    "record_type": "Decision",
    "profile_type": None,
    "project_id": "sys4ai",
    "namespace": "project/decisions",
    "scope": {"level": "project", "scope_id": "sys4ai", "parent_scopes": []},
    "title": "Use a provider-independent memory interface",
    "content": {
        "exact": "Agents call the Sys4AI Memory API rather than a provider directly.",
        "summary": "Keeps agents and canonical data portable.",
        "structured": {"decision": "provider_abstraction_required"},
    },
    "source": {
        "source_id": "src_prd_memory",
        "source_kind": "git_file",
        "path": "PRDs/Sys4AI_Memory_Service_PRD.md",
        "origin_uri": None,
        "locator": {"heading": "11.4 Why Cognee is not the public architecture"},
        "git_commit": "abc123",
        "git_blob_sha": None,
        "working_tree_state": None,
        "content_sha256": SHA_A,
    },
    "authority": {"tier": "A1", "trust_class": "human-approved", "canonical": True},
    "epistemic": {"status": "decision", "verification": "approved", "confidence": None},
    "lifecycle": {
        "status": "active",
        "valid_from": "2026-09-03T00:00:00Z",
        "valid_to": None,
        "supersedes": [],
        "superseded_by": [],
    },
    "security": {
        "sensitivity": "internal",
        "contains_secret": False,
        "retention_policy": "project_lifetime",
    },
    "processing": {
        "parsed_by": "markdown-adapter",
        "adapter_version": "1.0.0",
        "profile_id": "base@1",
        "deterministic_fields": ["title", "content.exact", "source.locator"],
        "model_extracted_fields": [],
        "model_id": None,
        "prompt_fingerprint": None,
        "processed_at": "2026-09-03T00:00:00Z",
    },
    "indexing": {
        "exact_fields": ["title", "content.structured.decision"],
        "lexical_fields": ["title", "content.exact"],
        "semantic_fields": ["content.summary"],
        "graph_enabled": True,
    },
    "created_at": "2026-09-03T00:00:00Z",
    "updated_at": "2026-09-03T00:00:00Z",
    "version": 1,
}

SOURCE_RECORD: dict[str, Any] = {
    "schema_version": "1.0",
    "api_version": "1.0",
    "source_id": "src_prd_memory",
    "project_id": "sys4ai",
    "path_or_uri": "PRDs/Sys4AI_Memory_Service_PRD.md",
    "path_pattern": None,
    "source_kind": "git_file",
    "format": "markdown",
    "canonicality": "canonical",
    "content_role": "authoritative",
    "authority_tier": "A1",
    "trust_class": "human-approved",
    "sensitivity": "internal",
    "namespace": "project/requirements",
    "scope": {"level": "project", "scope_id": "sys4ai", "parent_scopes": []},
    "profile_id": "base@1",
    "ingestion_adapter": "markdown-adapter",
    "chunking_profile": "markdown-structural@1",
    "schema_ref": None,
    "refresh_mode": "git-aware",
    "retention_policy": "project_lifetime",
    "owner": "project-director",
    "write_policy": "source-read-only",
    "include_flag": True,
    "notes": None,
    "content_sha256": SHA_A,
    "locator": {"path": "PRDs/Sys4AI_Memory_Service_PRD.md"},
    "git_commit": "abc123",
    "git_blob_sha": None,
    "working_tree_state": None,
    "origin_uri": None,
    "retrieved_at": None,
    "licensing_metadata": {},
    "access_metadata": {},
    "generated_from": [],
}

RELATION_RECORD: dict[str, Any] = {
    "schema_version": "1.0",
    "api_version": "1.0",
    "relation_id": "rel_01JTESTIMPLEMENTS",
    "project_id": "sys4ai",
    "relation_type": "IMPLEMENTS",
    "source_record_id": "mem_requirement_001",
    "target_record_id": "mem_component_memory_api",
    "source": {
        "source_id": "src_architecture",
        "locator": {"path": "docs/architecture.md", "heading": "Memory service"},
    },
    "validation": {"state": "deterministic", "confidence": None},
    "temporal": {"valid_from": "2026-09-03T00:00:00Z", "valid_to": None},
    "lifecycle": {"status": "active"},
}

WRITE_PROPOSAL: dict[str, Any] = {
    "schema_version": "1.0",
    "api_version": "1.0",
    "proposal_id": "mwp_01JTESTPROPOSAL",
    "idempotency_key": "agent-run-44:decision-candidate-2",
    "project_id": "sys4ai",
    "requester": {
        "principal_id": "agent_system_analyst",
        "agent_type": "system-analyst",
        "run_id": "run_44",
    },
    "requested_record_type": "Decision",
    "requested_scope": {"level": "project", "scope_id": "sys4ai", "parent_scopes": []},
    "requested_target": {"path": "Sys4AI/control_records/decisions/RDR-019.yaml"},
    "proposal": {"title": "Adopt memory profile versioning", "content": "proposed text"},
    "evidence": [{"record_id": "mem_01JTESTDECISION", "source_id": None}],
    "trust_class": "agent-generated",
    "sensitivity": "internal",
    "policy_result": {
        "action": "stage_for_review",
        "policy_id": "memory-write-policy@1",
        "reasons": ["Project-level decision requires approval"],
    },
    "status": "staged",
    "created_at": "2026-09-03T00:00:00Z",
}

RETRIEVAL_RESULT: dict[str, Any] = {
    "schema_version": "1.0",
    "api_version": "1.0",
    "request_id": "mrq_01JTESTQUERY",
    "project_id": "sys4ai",
    "query": "Why is the provider behind an adapter?",
    "mode": "hybrid",
    "evidence_state": "sufficient",
    "results": [
        {
            "record_id": "mem_01JTESTDECISION",
            "record_type": "Decision",
            "title": "Use a provider-independent memory interface",
            "content": "Agents call the Sys4AI Memory API.",
            "source": {
                "source_id": "src_prd_memory",
                "path": "PRDs/Sys4AI_Memory_Service_PRD.md",
                "origin_uri": None,
                "git_commit": "abc123",
                "content_sha256": SHA_A,
                "locator": {"heading": "11.4 Why Cognee is not the public architecture"},
            },
            "authority": {"tier": "A1", "trust_class": "human-approved"},
            "lifecycle": {"status": "active"},
            "scores": {
                "exact": 0.0,
                "lexical": 0.74,
                "semantic": 0.89,
                "graph": 1.0,
                "authority_boost": 0.2,
                "final": 0.93,
            },
            "selection_reason": [
                "semantic match",
                "linked architecture decision",
                "approved canonical source",
            ],
        }
    ],
    "filters_applied": {
        "project_scope": True,
        "permission": True,
        "current_only": True,
        "trust_minimum": "project-authored",
    },
    "trace_id": "trace_01JTESTQUERY",
}

MEMORY_PROFILE: dict[str, Any] = {
    "schema_version": "1.0",
    "api_version": "1.0",
    "profile_id": "research-agent",
    "version": "1.0.0",
    "extends": ["base@1"],
    "compatibility": {
        "sys4ai_memory_api": ">=1.0,<2.0",
        "required_capabilities": ["graph", "semantic", "exact"],
    },
    "record_types": [
        {
            "name": "Hypothesis",
            "schema_ref": "schemas/hypothesis.schema.json",
            "semantic_fields": ["summary"],
            "exact_fields": ["hypothesis_id", "statement"],
        },
        {
            "name": "Experiment",
            "schema_ref": "schemas/experiment.schema.json",
            "semantic_fields": [],
            "exact_fields": [],
        },
    ],
    "relations": ["TESTS", "SUPPORTS", "REFUTES"],
    "source_adapters": [{"id": "latex-research", "formats": ["tex", "bib"]}],
    "write_policies": [{"ref": "policies/research-write-policy.yaml"}],
    "retrieval_strategies": [{"ref": "retrieval/research-hybrid.yaml"}],
    "evaluations": [{"ref": "evals/research-memory-golden.yaml"}],
}

REBUILD_RECEIPT: dict[str, Any] = {
    "schema_version": "1.0",
    "api_version": "1.0",
    "receipt_id": "rbr_01JTESTREBUILD",
    "project_id": "sys4ai",
    "source_revisions": [
        {"source_id": "src_prd_memory", "revision": "abc123", "content_sha256": SHA_A}
    ],
    "configuration_fingerprint": SHA_B,
    "profile_versions": {"base": "1.0.0"},
    "adapter_versions": {"markdown-adapter": "1.0.0"},
    "provider_version": "1.5.3",
    "model_identifiers": [],
    "started_at": "2026-09-03T00:00:00Z",
    "completed_at": "2026-09-03T00:01:00Z",
    "warnings": [],
    "outcome": "succeeded",
    "trace_id": "trace_01JTESTREBUILD",
}

ERROR_ENVELOPE: dict[str, Any] = {
    "schema_version": "1.0",
    "api_version": "1.0",
    "error": {
        "category": "SOURCE_NOT_REGISTERED",
        "message": "The requested source is not registered.",
        "trace_id": "trace_01JTESTERROR",
        "recoverable": True,
        "remediation_hint": "Register the source and retry the request.",
    },
}

VALID_PAYLOADS: dict[str, dict[str, Any]] = {
    "memory-record.schema.json": MEMORY_RECORD,
    "source-record.schema.json": SOURCE_RECORD,
    "relation-record.schema.json": RELATION_RECORD,
    "write-proposal.schema.json": WRITE_PROPOSAL,
    "retrieval-result.schema.json": RETRIEVAL_RESULT,
    "memory-profile.schema.json": MEMORY_PROFILE,
    "rebuild-receipt.schema.json": REBUILD_RECEIPT,
    "error-envelope.schema.json": ERROR_ENVELOPE,
}


def invalid_payloads() -> dict[str, dict[str, Any]]:
    invalid = deepcopy(VALID_PAYLOADS)
    del invalid["memory-record.schema.json"]["record_id"]
    del invalid["source-record.schema.json"]["content_role"]
    invalid["relation-record.schema.json"]["relation_type"] = "implements"
    invalid["write-proposal.schema.json"]["evidence"] = []
    invalid["retrieval-result.schema.json"]["results"][0]["scores"]["final"] = 1.5
    invalid["memory-profile.schema.json"]["version"] = "1"
    invalid["rebuild-receipt.schema.json"]["configuration_fingerprint"] = "not-a-hash"
    invalid["error-envelope.schema.json"]["error"]["category"] = "RAW_PROVIDER_ERROR"
    return invalid

