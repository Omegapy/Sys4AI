from __future__ import annotations

import json
from pathlib import Path

import pytest

from sys4ai_memory.contracts import PUBLIC_OPERATION_CATALOG, AuthorityTier, MemoryProfile
from sys4ai_memory.profiles import (
    ProfileDefinition,
    ProfileError,
    ProfileSourceAuthority,
    assess_representation_change,
    load_profile,
    load_profile_set,
    validate_profile_registrations,
)
from sys4ai_memory.sources import load_profile_registry


def _payload(
    profile_id: str,
    *,
    extends: list[str] | None = None,
    record_type: str | None = None,
    relation: str | None = None,
    adapter: str | None = None,
    capabilities: list[str] | None = None,
    api: str = ">=1.0,<2.0",
    version: str = "1.0.0",
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "api_version": "1.0",
        "profile_id": profile_id,
        "version": version,
        "extends": extends or [],
        "compatibility": {
            "sys4ai_memory_api": api,
            "required_capabilities": capabilities or ["exact"],
        },
        "record_types": (
            [
                {
                    "name": record_type,
                    "schema_ref": "schemas/record.json",
                    "semantic_fields": ["content.exact"],
                    "exact_fields": ["record_id"],
                }
            ]
            if record_type
            else []
        ),
        "relations": [relation] if relation else [],
        "source_adapters": ([{"id": adapter, "formats": ["text"]}] if adapter else []),
        "write_policies": [{"ref": "base-write-policy"}],
        "retrieval_strategies": [{"ref": "base-ranking"}],
        "evaluations": [{"ref": "base-evaluation"}],
    }


def _write(root: Path, name: str, payload: dict[str, object]) -> Path:
    path = root / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _source_authority(tier: AuthorityTier) -> ProfileSourceAuthority:
    return ProfileSourceAuthority(
        source_ref="canonical-profile-registry:test",
        authority_tier=tier,
    )


def _write_reference(project: Path, relative_path: str) -> None:
    path = project / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("test fixture\n", encoding="utf-8")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "schemas").mkdir()
    (tmp_path / "schemas/record.json").write_text("{}\n", encoding="utf-8")
    return tmp_path


def test_profile_set_is_topologically_and_lexically_deterministic(project: Path) -> None:
    base = _write(
        project,
        "base.json",
        _payload("base@1", record_type="Statement", relation="CITES", adapter="text@1"),
    )
    beta = _write(
        project,
        "beta.json",
        _payload("beta@1", extends=["base@1"], record_type="BetaFact"),
    )
    alpha = _write(
        project,
        "alpha.json",
        _payload("alpha@1", extends=["base@1"], record_type="AlphaFact"),
    )

    first = load_profile_set(
        (beta, base, alpha),
        trusted_project_root=project,
        enabled_capabilities=frozenset({"exact"}),
    )
    second = load_profile_set(
        (alpha, beta, base),
        trusted_project_root=project,
        enabled_capabilities=frozenset({"exact"}),
    )

    assert first.profile_ids == ("base@1", "alpha@1", "beta@1")
    assert first.fingerprint == second.fingerprint
    assert first.record_type_owners["AlphaFact"] == "alpha@1"
    assert first.relation_owners == {"CITES": "base@1"}
    assert first.adapter_owners == {"text@1": "base@1"}


def test_tracked_base_and_software_engineering_profiles_are_complete() -> None:
    root = Path(__file__).resolve().parents[2]
    result = load_profile_set(
        (
            root / "profiles/base/profile.yaml",
            root / "profiles/software-engineering/profile.yaml",
        ),
        trusted_project_root=root,
        enabled_capabilities=frozenset(
            {
                "service_health",
                "source_registry",
                "ingestion",
                "exact",
                "lexical",
                "semantic",
                "graph",
                "provenance_explanation",
            }
        ),
        source_authorities={
            "base@1": ProfileSourceAuthority(
                source_ref="src_MEM-PROFILE-001",
                authority_tier=AuthorityTier.PROJECT_CONTROL,
            ),
            "software-engineering@1": ProfileSourceAuthority(
                source_ref="src_MEM-PROFILE-SE-001",
                authority_tier=AuthorityTier.PROJECT_CONTROL,
            ),
        },
    )

    assert result.profile_ids == ("base@1", "software-engineering@1")
    assert len(result.record_type_owners) == 18
    assert len(result.relation_owners) == 32
    assert len(result.adapter_owners) == 11
    assert result.record_type_owners["CodeSymbol"] == "software-engineering@1"
    assert result.adapter_owners["software-python-ast@1"] == "software-engineering@1"
    registrations = load_profile_registry(root / "registries/memory_profile_registry.csv")
    validate_profile_registrations(result, registrations)


def test_duplicate_yaml_keys_are_rejected(project: Path) -> None:
    profile = project / "duplicate.yaml"
    profile.write_text("profile_id: base@1\nprofile_id: changed@1\n", encoding="utf-8")
    with pytest.raises(ProfileError, match="duplicate YAML key"):
        load_profile(profile, trusted_project_root=project)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing_base", "required base profile is missing"),
        ("missing_parent", "profile dependency is missing"),
        ("cycle", "profile inheritance cycle"),
        ("detached", "does not extend base@1"),
        ("capability", "requires disabled capabilities"),
        ("api", "incompatible with memory API"),
        ("conflict", "conflicts with base@1 on record type"),
    ],
)
def test_profile_set_fails_closed(project: Path, mutation: str, message: str) -> None:
    base_payload = _payload("base@1", record_type="Statement")
    extension_payload = _payload(
        "extension@1",
        extends=["base@1"],
        record_type="ExtensionFact",
    )
    selected = ("base", "extension")
    capabilities = frozenset({"exact"})
    if mutation == "missing_base":
        selected = ("extension",)
    elif mutation == "missing_parent":
        extension_payload["extends"] = ["absent@1"]
    elif mutation == "cycle":
        extension_payload["extends"] = ["extension@1"]
    elif mutation == "detached":
        extension_payload["extends"] = []
    elif mutation == "capability":
        extension_payload["compatibility"] = {
            "sys4ai_memory_api": ">=1.0,<2.0",
            "required_capabilities": ["semantic"],
        }
    elif mutation == "api":
        extension_payload["compatibility"] = {
            "sys4ai_memory_api": ">=2.0,<3.0",
            "required_capabilities": ["exact"],
        }
    elif mutation == "conflict":
        extension_payload["record_types"] = base_payload["record_types"]

    paths = {
        "base": _write(project, "base.json", base_payload),
        "extension": _write(project, "extension.json", extension_payload),
    }
    with pytest.raises(ProfileError, match=message):
        load_profile_set(
            tuple(paths[name] for name in selected),
            trusted_project_root=project,
            enabled_capabilities=capabilities,
        )


def test_profile_path_and_references_are_confined(project: Path, tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-profile.json"
    outside.write_text(json.dumps(_payload("base@1")), encoding="utf-8")
    with pytest.raises(ProfileError, match="escapes"):
        load_profile(outside, trusted_project_root=project)

    unsafe = _payload("base@1", record_type="Statement")
    record_types = unsafe["record_types"]
    assert isinstance(record_types, list)
    record_types[0]["schema_ref"] = "schemas/missing.json"
    profile = _write(project, "unsafe.json", unsafe)
    with pytest.raises(ProfileError, match="unsafe or missing reference"):
        load_profile_set(
            (profile,),
            trusted_project_root=project,
            enabled_capabilities=frozenset({"exact"}),
        )


def test_representation_changes_require_rebuild() -> None:
    previous = MemoryProfile.model_validate(_payload("base@1", record_type="Statement"))
    unchanged = MemoryProfile.model_validate(_payload("base@1", record_type="Statement"))
    changed = MemoryProfile.model_validate(
        _payload("base@1", record_type="Statement", relation="CITES", version="1.1.0")
    )

    assert assess_representation_change(previous, unchanged).changed is False
    result = assess_representation_change(previous, changed)
    assert result.changed is True
    assert result.requires_rebuild is True
    assert result.reasons == ("stored representation inputs changed",)


def test_generic_extension_declares_all_profile_behavior_without_changing_base_api(
    project: Path,
) -> None:
    base = _write(project, "base.json", _payload("base@1", record_type="Statement"))
    extension_payload = _payload(
        "extension@1",
        extends=["base@1"],
        record_type="DomainFact",
        relation="DESCRIBES_DOMAIN",
        adapter="domain-adapter@1",
        capabilities=["exact", "lexical", "semantic"],
    )
    record_types = extension_payload["record_types"]
    assert isinstance(record_types, list)
    record_types[0]["lexical_fields"] = ["title", "content.exact"]
    extension_payload.update(
        {
            "write_policies": [{"ref": "policies/domain-write.yaml", "authority_tier": "A5"}],
            "retrieval_strategies": [
                {"ref": "retrieval/domain-query.yaml", "authority_tier": "A5"}
            ],
            "retention_policies": [
                {"ref": "policies/domain-retention.yaml", "authority_tier": "A5"}
            ],
            "context_assembly_rules": [
                {"ref": "retrieval/domain-context.yaml", "authority_tier": "A5"}
            ],
            "reranking_rules": [{"ref": "retrieval/domain-rerank.yaml", "authority_tier": "A5"}],
            "instructions": [{"ref": "instructions/domain-memory.yaml", "authority_tier": "A5"}],
            "evaluations": [{"ref": "evals/domain-golden.yaml"}],
        }
    )
    for reference in (
        "policies/domain-write.yaml",
        "retrieval/domain-query.yaml",
        "policies/domain-retention.yaml",
        "retrieval/domain-context.yaml",
        "retrieval/domain-rerank.yaml",
        "instructions/domain-memory.yaml",
        "evals/domain-golden.yaml",
    ):
        _write_reference(project, reference)
    extension = _write(project, "extension.json", extension_payload)
    public_fields_before = tuple(MemoryProfile.model_fields)
    operations_before = tuple(item.name for item in PUBLIC_OPERATION_CATALOG)

    result = load_profile_set(
        (extension, base),
        trusted_project_root=project,
        enabled_capabilities=frozenset({"exact", "lexical", "semantic"}),
        source_authorities={
            "extension@1": _source_authority(AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE)
        },
    )

    loaded = result.profiles[1]
    assert result.profile_ids == ("base@1", "extension@1")
    assert loaded.profile.record_types[0].lexical_fields == ("title", "content.exact")
    assert loaded.profile.query_strategies == loaded.profile.retrieval_strategies
    assert loaded.profile.retention_policies[0].ref == "policies/domain-retention.yaml"
    assert loaded.profile.context_assembly_rules[0].ref == "retrieval/domain-context.yaml"
    assert loaded.profile.reranking_rules[0].ref == "retrieval/domain-rerank.yaml"
    assert loaded.profile.instructions[0].authority_tier is AuthorityTier.AGENT_DURABLE_MATERIAL
    assert result.source_authorities["extension@1"] == loaded.source_authority
    assert tuple(MemoryProfile.model_fields) == public_fields_before
    assert tuple(item.name for item in PUBLIC_OPERATION_CATALOG) == operations_before


def test_extension_schema_exposes_generic_fields_and_authority_metadata() -> None:
    schema = ProfileDefinition.model_json_schema()

    assert {
        "retention_policies",
        "context_assembly_rules",
        "reranking_rules",
        "instructions",
    } <= set(schema["properties"])
    assert "lexical_fields" in schema["$defs"]["ProfileRecordTypeDefinition"]["properties"]
    assert "authority_tier" in schema["$defs"]["ProfileBehaviorReference"]["properties"]


@pytest.mark.parametrize(
    "field",
    [
        "write_policies",
        "retrieval_strategies",
        "retention_policies",
        "context_assembly_rules",
        "reranking_rules",
        "instructions",
    ],
)
def test_every_instruction_bearing_declaration_obeys_source_authority(
    project: Path,
    field: str,
) -> None:
    base = _write(project, "base.json", _payload("base@1", record_type="Statement"))
    extension_payload = _payload(
        "extension@1",
        extends=["base@1"],
        record_type="DomainFact",
    )
    extension_payload[field] = [{"ref": f"{field}@1", "authority_tier": "A3"}]
    extension = _write(project, "extension.json", extension_payload)

    with pytest.raises(ProfileError, match="exceeding source authority A7"):
        load_profile_set(
            (base, extension),
            trusted_project_root=project,
            enabled_capabilities=frozenset({"exact"}),
        )
    with pytest.raises(ProfileError, match="exceeding source authority A4"):
        load_profile_set(
            (base, extension),
            trusted_project_root=project,
            enabled_capabilities=frozenset({"exact"}),
            source_authorities={"extension@1": _source_authority(AuthorityTier.EXTERNAL_EVIDENCE)},
        )

    result = load_profile_set(
        (base, extension),
        trusted_project_root=project,
        enabled_capabilities=frozenset({"exact"}),
        source_authorities={"extension@1": _source_authority(AuthorityTier.PROJECT_CONTROL)},
    )
    assert result.source_authorities["extension@1"].authority_tier is AuthorityTier.PROJECT_CONTROL


def test_authority_mapping_is_exact_and_part_of_the_profile_fingerprint(project: Path) -> None:
    base = _write(project, "base.json", _payload("base@1", record_type="Statement"))
    extension_payload = _payload(
        "extension@1",
        extends=["base@1"],
        record_type="DomainFact",
    )
    extension_payload["instructions"] = [{"ref": "domain-instructions@1", "authority_tier": "A5"}]
    extension = _write(project, "extension.json", extension_payload)

    stronger = load_profile_set(
        (base, extension),
        trusted_project_root=project,
        enabled_capabilities=frozenset({"exact"}),
        source_authorities={
            "extension@1": _source_authority(AuthorityTier.CANONICAL_PROJECT_KNOWLEDGE)
        },
    )
    weaker = load_profile_set(
        (extension, base),
        trusted_project_root=project,
        enabled_capabilities=frozenset({"exact"}),
        source_authorities={"extension@1": _source_authority(AuthorityTier.AGENT_DURABLE_MATERIAL)},
    )
    assert stronger.fingerprint != weaker.fingerprint

    with pytest.raises(ProfileError, match="unknown profile IDs: misspelled@1"):
        load_profile_set(
            (base, extension),
            trusted_project_root=project,
            enabled_capabilities=frozenset({"exact"}),
            source_authorities={"misspelled@1": _source_authority(AuthorityTier.PROJECT_CONTROL)},
        )


def test_extension_behavior_references_remain_project_confined(project: Path) -> None:
    base = _write(project, "base.json", _payload("base@1", record_type="Statement"))
    extension_payload = _payload(
        "extension@1",
        extends=["base@1"],
        record_type="DomainFact",
    )
    extension_payload["context_assembly_rules"] = [{"ref": "retrieval/missing-context.yaml"}]
    extension = _write(project, "extension.json", extension_payload)

    with pytest.raises(ProfileError, match="unsafe or missing reference"):
        load_profile_set(
            (base, extension),
            trusted_project_root=project,
            enabled_capabilities=frozenset({"exact"}),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("retention_policies", [{"ref": "retention@1"}]),
        ("context_assembly_rules", [{"ref": "context@1"}]),
        ("reranking_rules", [{"ref": "rerank@1"}]),
        ("instructions", [{"ref": "instructions@1"}]),
    ],
)
def test_extension_representation_changes_require_rebuild(
    field: str,
    value: list[dict[str, str]],
) -> None:
    previous = loadable = _payload("base@1", record_type="Statement")
    changed = {**loadable, field: value}

    previous_profile = load_profile_definition(previous)
    changed_profile = load_profile_definition(changed)
    result = assess_representation_change(previous_profile, changed_profile)

    assert result.changed is True
    assert result.requires_rebuild is True
    assert result.reasons == ("stored representation inputs changed",)


def test_evaluation_only_change_does_not_require_rebuild() -> None:
    previous = _payload("base@1", record_type="Statement")
    changed = {**previous, "evaluations": [{"ref": "changed-evaluation@1"}]}

    result = assess_representation_change(
        load_profile_definition(previous),
        load_profile_definition(changed),
    )

    assert result.changed is False
    assert result.requires_rebuild is False


def test_index_field_change_requires_rebuild() -> None:
    previous = _payload("base@1", record_type="Statement")
    changed = json.loads(json.dumps(previous))
    record_types = changed["record_types"]
    assert isinstance(record_types, list)
    record_types[0]["lexical_fields"] = ["content.exact"]

    result = assess_representation_change(
        load_profile_definition(previous),
        load_profile_definition(changed),
    )

    assert result.changed is True
    assert result.requires_rebuild is True


@pytest.mark.parametrize(
    "field",
    [
        "write_policies",
        "retrieval_strategies",
        "retention_policies",
        "context_assembly_rules",
        "reranking_rules",
        "instructions",
        "evaluations",
    ],
)
def test_duplicate_extension_references_fail_schema_validation(
    project: Path,
    field: str,
) -> None:
    payload = _payload("base@1", record_type="Statement")
    payload[field] = [{"ref": "duplicate@1"}, {"ref": "duplicate@1"}]
    profile = _write(project, "duplicate-reference.json", payload)

    with pytest.raises(ProfileError, match="must not contain duplicates"):
        load_profile(profile, trusted_project_root=project)


def test_duplicate_index_fields_fail_schema_validation(project: Path) -> None:
    payload = _payload("base@1", record_type="Statement")
    record_types = payload["record_types"]
    assert isinstance(record_types, list)
    record_types[0]["lexical_fields"] = ["content.exact", "content.exact"]
    profile = _write(project, "duplicate-index-field.json", payload)

    with pytest.raises(ProfileError, match="lexical_fields must not contain duplicates"):
        load_profile(profile, trusted_project_root=project)


def load_profile_definition(payload: dict[str, object]) -> ProfileDefinition:
    return ProfileDefinition.model_validate(payload)
