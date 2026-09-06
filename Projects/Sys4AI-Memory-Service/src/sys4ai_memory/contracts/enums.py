"""Stable enum values defined by PRD sections 14 through 18 and 24.3."""

from __future__ import annotations

from enum import StrEnum


class MemoryScope(StrEnum):
    SYSTEM = "system"
    WORKSPACE = "workspace"
    PROJECT = "project"
    AGENT_TYPE = "agent_type"
    AGENT_INSTANCE = "agent_instance"
    TASK = "task"
    SESSION = "session"
    USER = "user"


class AuthorityTier(StrEnum):
    SYSTEM_POLICY = "A0"
    SYS4AI_GOVERNANCE = "A1"
    PROJECT_CONTROL = "A2"
    CANONICAL_PROJECT_KNOWLEDGE = "A3"
    EXTERNAL_EVIDENCE = "A4"
    AGENT_DURABLE_MATERIAL = "A5"
    SESSION_SCRATCH = "A6"
    UNTRUSTED_CONTENT = "A7"


class TrustClass(StrEnum):
    SYSTEM_CONTROLLED = "system-controlled"
    HUMAN_APPROVED = "human-approved"
    SCHEMA_VALIDATED = "schema-validated"
    PROJECT_AUTHORED = "project-authored"
    EXTERNALLY_AUTHENTICATED = "externally-authenticated"
    EXTERNAL_UNVERIFIED = "external-unverified"
    AGENT_GENERATED = "agent-generated"
    MODEL_EXTRACTED = "model-extracted"
    USER_SUPPLIED = "user-supplied"
    UNTRUSTED = "untrusted"


class RecordStatus(StrEnum):
    PROPOSED = "proposed"
    STAGED = "staged"
    APPROVED = "approved"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"
    DELETED = "deleted"


class EpistemicStatus(StrEnum):
    SOURCE_STATEMENT = "source_statement"
    OBSERVATION = "observation"
    CLAIM = "claim"
    FACT_CANDIDATE = "fact_candidate"
    VERIFIED_FACT = "verified_fact"
    HYPOTHESIS = "hypothesis"
    INFERENCE = "inference"
    DECISION = "decision"
    PROCEDURE = "procedure"
    PREFERENCE = "preference"
    CONSTRAINT = "constraint"
    RESULT = "result"
    COUNTEREXAMPLE = "counterexample"
    UNKNOWN = "unknown"


class CoreRecordType(StrEnum):
    SOURCE_ARTIFACT = "SourceArtifact"
    SOURCE_FRAGMENT = "SourceFragment"
    ENTITY = "Entity"
    STATEMENT = "Statement"
    REQUIREMENT = "Requirement"
    DECISION = "Decision"
    PROCEDURE = "Procedure"
    EVENT = "Event"
    OBSERVATION = "Observation"
    OUTCOME = "Outcome"
    FEEDBACK = "Feedback"
    RELATION = "Relation"
    TOMBSTONE = "Tombstone"
    EXTENSION_RECORD = "ExtensionRecord"


class CoreRelation(StrEnum):
    CONTAINS = "CONTAINS"
    DEFINES = "DEFINES"
    DESCRIBES = "DESCRIBES"
    IMPLEMENTS = "IMPLEMENTS"
    VALIDATES = "VALIDATES"
    DEPENDS_ON = "DEPENDS_ON"
    BLOCKS = "BLOCKS"
    ENABLES = "ENABLES"
    DERIVED_FROM = "DERIVED_FROM"
    GENERATED_FROM = "GENERATED_FROM"
    CITES = "CITES"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    SUPERSEDES = "SUPERSEDES"
    INVALIDATES = "INVALIDATES"
    APPLIES_TO = "APPLIES_TO"
    OWNED_BY = "OWNED_BY"
    CREATED_BY = "CREATED_BY"
    REVIEWED_BY = "REVIEWED_BY"
    OBSERVED_DURING = "OBSERVED_DURING"
    RESULTED_IN = "RESULTED_IN"
    SIMILAR_TO = "SIMILAR_TO"
    RELATED_TO = "RELATED_TO"
    HAS_SOURCE = "HAS_SOURCE"
    HAS_EVIDENCE = "HAS_EVIDENCE"
    HAS_STATUS = "HAS_STATUS"
    USES = "USES"
    PRODUCES = "PRODUCES"


class Sensitivity(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    SECRET_PROHIBITED = "secret-prohibited"  # noqa: S105 - PRD classification label


class SourceRole(StrEnum):
    AUTHORITATIVE = "authoritative"
    EVIDENTIAL = "evidential"
    GENERATED = "generated"
    EPISODIC = "episodic"
    SCRATCH = "scratch"


class RetrievalMode(StrEnum):
    EXACT = "exact"
    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    GRAPH = "graph"
    TEMPORAL = "temporal"
    HYBRID = "hybrid"


class EvidenceState(StrEnum):
    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"


class PolicyAction(StrEnum):
    REJECT = "reject"
    SESSION_ONLY = "session_only"
    EPISODIC_COMMIT = "episodic_commit"
    DERIVED_COMMIT = "derived_commit"
    STAGE_FOR_REVIEW = "stage_for_review"
    CANONICAL_PROMOTION = "canonical_promotion"


class Permission(StrEnum):
    READ = "read"
    PROPOSE = "propose"
    WRITE_DERIVED = "write-derived"
    APPROVE = "approve"
    DELETE = "delete"
    SHARE = "share"
    REBUILD = "rebuild"
    ADMINISTER = "administer"
