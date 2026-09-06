"""Declarative extension fields layered over the stable memory-profile contract."""

from __future__ import annotations

from typing import Self

from pydantic import field_validator, model_validator

from sys4ai_memory.contracts import AuthorityTier, MemoryProfile
from sys4ai_memory.contracts._base import (
    ContractModel,
    StableIdentifier,
    reject_sensitive_error_text,
)
from sys4ai_memory.contracts.models import (
    FieldPath,
    ProfileRecordType,
    ProfileReference,
)


class ProfileRecordTypeDefinition(ProfileRecordType):
    """Record declaration with fields for every supported index channel."""

    lexical_fields: tuple[FieldPath, ...] = ()

    @model_validator(mode="after")
    def validate_index_fields(self) -> Self:
        collections = {
            "semantic_fields": self.semantic_fields,
            "exact_fields": self.exact_fields,
            "lexical_fields": self.lexical_fields,
        }
        for label, values in collections.items():
            if len(values) != len(set(values)):
                raise ValueError(f"profile record {label} must not contain duplicates")
        return self


class ProfileBehaviorReference(ProfileReference):
    """Opaque behavior reference with an explicit maximum authority tier."""

    authority_tier: AuthorityTier = AuthorityTier.UNTRUSTED_CONTENT

    @field_validator("ref")
    @classmethod
    def validate_ref(cls, value: str) -> str:
        return reject_sensitive_error_text(value, "profile behavior reference")


class ProfileSourceAuthority(ContractModel):
    """Authority granted by trusted registry state, never by profile content."""

    source_ref: StableIdentifier
    authority_tier: AuthorityTier

    @field_validator("source_ref")
    @classmethod
    def validate_source_ref(cls, value: str) -> str:
        return reject_sensitive_error_text(value, "profile source reference")


class ProfileDefinition(MemoryProfile):
    """Loaded profile plus optional, backward-compatible extension declarations."""

    record_types: tuple[ProfileRecordTypeDefinition, ...]
    write_policies: tuple[ProfileBehaviorReference, ...]
    retrieval_strategies: tuple[ProfileBehaviorReference, ...]
    retention_policies: tuple[ProfileBehaviorReference, ...] = ()
    context_assembly_rules: tuple[ProfileBehaviorReference, ...] = ()
    reranking_rules: tuple[ProfileBehaviorReference, ...] = ()
    instructions: tuple[ProfileBehaviorReference, ...] = ()

    @property
    def query_strategies(self) -> tuple[ProfileBehaviorReference, ...]:
        """Use the PRD query-strategy term for retrieval strategy declarations."""

        return self.retrieval_strategies

    def behavior_references(
        self,
    ) -> tuple[tuple[str, ProfileBehaviorReference], ...]:
        """Return every instruction-bearing declaration with its policy domain."""

        collections = (
            ("write policy", self.write_policies),
            ("query strategy", self.retrieval_strategies),
            ("retention policy", self.retention_policies),
            ("context assembly rule", self.context_assembly_rules),
            ("reranking rule", self.reranking_rules),
            ("instruction", self.instructions),
        )
        return tuple((kind, reference) for kind, values in collections for reference in values)

    @model_validator(mode="after")
    def validate_behavior_references(self) -> Self:
        collections = {
            "write policy references": self.write_policies,
            "query strategy references": self.retrieval_strategies,
            "retention policy references": self.retention_policies,
            "context assembly references": self.context_assembly_rules,
            "reranking references": self.reranking_rules,
            "instruction references": self.instructions,
            "evaluation references": self.evaluations,
        }
        for label, values in collections.items():
            refs = tuple(item.ref for item in values)
            if len(refs) != len(set(refs)):
                raise ValueError(f"profile {label} must not contain duplicates")
        return self
