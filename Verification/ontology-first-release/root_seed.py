"""Prepare reviewable root seed documents from exact, selected local sources.

This script writes only release evidence. The installed ontology publisher owns
the separate canonical publication step.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CORE = "urn:sys4ai:ontology:core:"
NAMESPACE = "urn:sys4ai:ontology:project:sys4ai-depot:"
CONTEXT = "ONTOLOGY/contexts/context-v1.jsonld"


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def prepare(root: Path, output: Path):
    root = root.resolve(strict=True)
    documents = {name: [] for name in ("project", "skills", "roles", "artifacts", "projects")}
    sources = {}

    def source(relative, locator):
        path = root / relative
        for part in [path, *path.parents]:
            if part == root.parent:
                break
            if part.is_symlink():
                raise ValueError(f"Symlink source: {relative}")
        data = path.read_bytes()
        if locator.startswith("/"):
            locator = "json:" + locator
        elif not locator.startswith(("section:", "line:", "lines:", "json:")):
            locator = "section:" + locator.split(";")[0].strip()
        item = {"path": relative, "sha256": hashlib.sha256(data).hexdigest(), "locator": locator}
        sources[(relative, locator)] = item
        return item

    def record(local, label, definition, type_name, src, *, group="project", kind="instance", **extra):
        item = {"@id": NAMESPACE + local, "@type": [CORE + type_name], "kind": kind,
                "label": label, "definition": definition, "lifecycle": "approved", "module": "project",
                "sources": src if isinstance(src, list) else [src], "fact_kind": "asserted", **extra}
        if kind != "binding":
            group = "project"
        documents[group].append(item)
        return item["@id"]

    def relation(local, subject, predicate, target, definition, src, *, group="project"):
        return record(local, definition, definition, "Relationship", src, group=group, kind="relation",
                      subject=subject, predicate=CORE + predicate, object=target)

    def binding(local, entity, binding_type, src, *, group="artifacts", definition=None):
        return record(local, "Source binding " + local,
                      definition or "This explicit binding traces the selected entity to its current local source.",
                      "SourceBinding", src, group=group, kind="binding", entity=entity, binding_type=binding_type)

    def artifact(local, label, relative, locator, *, type_name="Artifact"):
        src = source(relative, locator)
        entity = record(local, label, f"The selected project-local source at {relative}.", type_name, src, group="artifacts")
        binding("binding-" + local, entity, "specification" if type_name == "Specification" else "artifact", src)
        return entity, src

    soul, soul_src = artifact("artifact-soul", "Root reasoning and verification guidance", "SOUL.md", "Verification discipline; Validation discipline")
    agents, agents_src = artifact("artifact-agents", "Root project instructions", "AGENTS.md", "Project identity and boundaries; Task-system workflow")
    director_file, director_src = artifact("artifact-director-role", "Root Director role definition", "ROLE.md", "Authority and non-authority; Task activation and ownership")
    specs, specs_src = artifact("artifact-specifications", "Root technical specifications", "SPECS.md", "Ontology first release and initialization v8", type_name="Specification")
    registry, registry_src = artifact("artifact-registry", "Factual workspace registry", "depot/projects.json", "/projects")
    module_artifact, module_src = artifact("artifact-core-module", "Selected reusable core module", "ONTOLOGY/modules/sys4ai-core/1.0.0/core.jsonld", "/@graph")
    template_mapping, mapping_src = artifact("artifact-template-mapping", "Explicit Template update mapping", "depot/template-update.json", "/overrides")

    for name, src, text in [
        ("Project", agents_src, "The root is a depot manager; registration is factual inventory and grants no project write authority."),
        ("Task", source(".agents/skills/task/SKILL.md", "Intake and mode; Bootstrap and the real manager"), "A governed Task requires explicit activation and remains separate from a TRD, implementation plan, native goal and conversation."),
        ("TRD", source(".agents/skills/to-trd/SKILL.md", "1. Activation and authority; 6. Maintain the document state"), "A TRD captures approved requirements. Creating or approving it does not create a Task or authorize implementation."),
        ("ImplementationPlan", source(".agents/skills/to-implementation-plan/SKILL.md", "Activation boundary; State-system boundary"), "A managed implementation plan records planned work; its state is separate from execution and Task state."),
        ("NativeGoal", director_src, "Native goal state is separate from managed plans, TRDs, Tasks and Git state."),
        ("CodexConversation", director_src, "A Codex conversation is not the canonical project Task ledger."),
        ("Verification", soul_src, "Verification checks conformance to requirements and the stated design."),
        ("Validation", soul_src, "Validation checks fitness for the user's intended project use."),
        ("MemoryRecord", source(".agents/skills/memory/SKILL.md", "Project memory"), "Project memory retains portable historical evidence; current governance and Task ownership remain controlling."),
    ]:
        binding("binding-concept-" + name, CORE + name, "artifact", src, definition=text)

    role_data = [
        ("host-director", "Sys4AI host Project Director", "The host frames project work and owns workspace registration and reusable adoption decisions; an activated Task manager owns its exact assigned execution.", [(agents, agents_src), (director_file, director_src)], ["depot Director"]),
        ("confirmed-task-manager", "Sys4AI confirmed Task manager role", "This persisted role can coordinate exactly one assigned Task only after a real native receipt and explicit manager activation. Reading the role does not establish a live manager.", [], ["installed Task manager role"]),
        ("ordinary-child", "Sys4AI ordinary project sub-agent role", "An ordinary child performs one bounded assignment and returns evidence; it has no canonical Task, role-index or shared publication ownership.", [], ["bounded project worker"]),
    ]
    role_ids = {}
    for local, label, definition, artifacts, aliases in role_data:
        if not artifacts:
            folder = "task-manager" if local == "confirmed-task-manager" else "project-sub-agent"
            for filename in ("AGENTS.md", "ROLE.md"):
                artifacts.append(artifact("artifact-" + folder + "-" + filename.split(".")[0].lower(),
                                          folder + " " + filename + " source", f"Roles/{folder}/{filename}",
                                          "Required first reads" if filename == "AGENTS.md" else "Purpose; Authority limits"))
        srcs = [s for _, s in artifacts]
        role_ids[local] = record(local, label, definition, "Role", srcs, group="roles", aliases=aliases)
        binding("binding-" + local, role_ids[local], "role", srcs, group="roles", definition=definition)
        for i, (artifact_id, src) in enumerate(artifacts):
            relation(local + "-defined-by-" + str(i), role_ids[local], "definedBy", artifact_id,
                     label + " is defined by its selected source " + str(i + 1), src, group="roles")
    relation("manager-manages-task", role_ids["confirmed-task-manager"], "manages", CORE + "Task",
             "A confirmed Task manager coordinates its assigned governed Task", role_data[1][3][0][1], group="roles")
    binding("binding-concept-TaskManager", CORE + "TaskManager", "role", [s for _, s in role_data[1][3]], group="roles")

    authority = record("ontology-publication-authority", "Scoped ontology publication authority",
                       "A current local Director or confirmed Task manager may publish only an exact reviewed ontology change within its granted scope. Validation and memory publication grants do not provide this authority.",
                       "Authority", [director_src, specs_src], group="project")
    memory_authority = record("memory-publication-authority", "Scoped memory publication authority",
                              "The memory publisher requires reviewed record bytes and a current memory-only grant. It does not publish or redefine ontology semantics.",
                              "Authority", source(".agents/skills/memory/references/publication-examples.md", "Preparing reviewed publication"))

    skills = [
        ("memory", "Project memory retrieval", "capability-memory-retrieval", ["retrieve project lessons", "retrieve prior project decisions"],
         "Retrieve current eligible project memory with source evidence and explicit limitations. Historical records grant no execution or publication authority.", "MemoryRecord"),
        ("to-trd", "TRD creation", "capability-trd-creation", ["capture requirements", "create requirements document"],
         "Discover user intent and create a managed TRD only through explicit to-trd activation. TRD creation does not create a Task or authorize implementation.", "TRD"),
        ("task", "Governed Task management", "capability-task-management", ["manage governed work", "activate project Task"],
         "Route explicitly activated project Task work under the installed ownership and required-team gates. Mentioning a task does not activate this workflow.", "Task"),
        ("agent-task", "Canonical Task ledger operations", "capability-task-ledger", ["inspect Task state", "record Task response"],
         "Inspect or mutate the canonical project Task ledger using its current helper and exact actor, revision and execution gates.", "Task"),
        ("ontology", "Project ontology retrieval", "capability-ontology-retrieval", ["resolve ontology terms", "find semantic relationships"],
         "Resolve selected ontology definitions, capabilities and typed relationships without invoking discovered operations or granting authority.", "OntologyConcept"),
    ]
    skill_locators = {"memory": "Project memory", "to-trd": "1. Activation and authority",
                      "task": "Intake and mode", "agent-task": "Authority and root",
                      "ontology": "Ontology"}
    for name, label, capability_local, aliases, definition, target_type in skills:
        art, src = artifact("artifact-skill-" + name, "Installed " + name + " skill source", f".agents/skills/{name}/SKILL.md", skill_locators[name])
        skill_id = record("installed-" + name, "Installed " + name + " skill", definition, "Skill", src,
                          group="skills", aliases=[name + " skill installation"])
        cap_id = record(capability_local, label, definition, "Capability", src, group="skills", aliases=aliases)
        binding("binding-skill-" + name, skill_id, "skill", src, group="skills", definition=definition)
        relation(name + "-defined-by", skill_id, "definedBy", art, name + " skill is defined by its installed SKILL.md", src, group="skills")
        relation(name + "-provides", skill_id, "providesCapability", cap_id, name + " skill provides " + label, src, group="skills")
        shared_capability = {"memory": "MemoryRetrieval", "to-trd": "TRDCreation", "task": "TaskManagement",
                             "agent-task": "TaskManagement", "ontology": "OntologyRetrieval"}[name]
        relation(name + "-provides-shared", skill_id, "providesCapability", CORE + shared_capability,
                 name + " skill implements the shared " + shared_capability + " capability", src, group="skills")
        relation(name + "-capability-meaning", cap_id, "relatedTo", CORE + shared_capability,
                 label + " uses the shared capability meaning", src, group="skills")
        if name in {"memory", "ontology"}:
            relation(name + "-retrieves", cap_id, "retrieves", CORE + target_type, label + " retrieves " + target_type, src, group="skills")
        elif name == "to-trd":
            relation(name + "-produces", skill_id, "produces", CORE + target_type, "TRD creation produces a requirements document", src, group="skills")
        relation(name + "-governed-by", skill_id, "governedBy", art, name + " operations follow current installed source instructions", src, group="skills")
    relation("memory-publish-requires-authority", NAMESPACE + "installed-memory", "requiresAuthority", memory_authority,
             "Memory publication requires its own current grant", source(".agents/skills/memory/references/publication-examples.md", "Preparing reviewed publication"), group="skills")
    relation("ontology-publish-requires-authority", NAMESPACE + "installed-ontology", "requiresAuthority", authority,
             "Ontology publication requires its own reviewed grant", specs_src, group="skills")

    registry_value = json.loads((root / "depot/projects.json").read_text())
    for entry in registry_value["projects"]:
        local = "depot" if entry["id"] == "sys4ai-depot" else "registered-template" if entry["kind"] == "project-template" else "registered-" + entry["id"]
        kind = "ProjectTemplate" if entry["kind"] == "project-template" else "Project"
        definition = (f"Registry representation of {entry['name']} at {entry['path']}. "
                      "This record describes factual inventory only; it imports no internal vocabulary and grants no read, write or publication authority over that project.")
        entity = record(local, "Registered " + entry["name"], definition, kind, registry_src,
                        group="projects", fact_kind="external", scope_note="Only the registry entry is represented; no child-project files are loaded.")
        binding("binding-project-" + entry["id"], entity, "registry", registry_src, group="projects", definition=definition)
        relation("registry-describes-" + local, registry, "describes", entity, "The registry describes " + entry["name"], registry_src, group="projects")
        if local == "depot":
            relation("depot-has-director", entity, "hasRole", role_ids["host-director"], "The depot host has its local Director role", director_src, group="projects")
        if kind == "ProjectTemplate":
            relation("template-derives-core", entity, "derivesFrom", module_artifact, "Template vocabulary derives from the selected reusable core source", [module_src, mapping_src], group="projects")
            relation("template-derives-mapping", entity, "derivesFrom", template_mapping, "Template distribution follows the explicit reusable source mapping", mapping_src, group="projects")

    destinations = {"project": "ONTOLOGY/modules/project/project.jsonld",
                    **{name: "ONTOLOGY/bindings/" + name + ".json" for name in ("skills", "roles", "artifacts", "projects")}}
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": 1, "project_id": "sys4ai-depot", "documents": [],
                "source_allowlist": sorted({s["path"] for s in sources.values()}),
                "review": "Source-backed initial definitions and explicit bindings under PLAN-20260909-731308FD; publish separately through the exact reviewed ontology operation."}
    for name, records in documents.items():
        value = {"@context": CONTEXT, "@graph": sorted(records, key=lambda x: x["@id"])}
        data = encode(value)
        (output / (name + ".json")).write_bytes(data)
        manifest["documents"].append({"source": name + ".json", "destination": destinations[name],
                                      "sha256": hashlib.sha256(data).hexdigest(), "records": len(records)})
    competency = {"schema_version": 1, "questions": [
        {"id": "root-task-source", "intent": "definition", "query": "Task", "expected_ids": [CORE + "Task"],
         "expected_sources": [".agents/skills/task/SKILL.md"], "expected_terms": ["distinct from a TRD", "Document approval does not activate a Task"]},
        {"id": "root-trd-boundary", "intent": "definition", "query": "TRD", "expected_ids": [CORE + "TRD"],
         "expected_sources": [".agents/skills/to-trd/SKILL.md"], "expected_terms": ["does not create a Task"]},
        {"id": "root-memory-capability", "intent": "capability", "query": "memory retrieval",
         "expected_ids": [CORE + "MemoryRetrieval", NAMESPACE + "installed-memory"], "expected_sources": [".agents/skills/memory/SKILL.md"]},
        {"id": "root-skill-to-capability", "intent": "capability", "query": "Installed memory skill",
         "expected_ids": [NAMESPACE + "installed-memory", NAMESPACE + "capability-memory-retrieval", CORE + "MemoryRetrieval"]},
        {"id": "root-trd-capability", "intent": "capability", "query": "TRDCreation",
         "expected_ids": [NAMESPACE + "installed-to-trd"], "expected_sources": [".agents/skills/to-trd/SKILL.md"], "expected_terms": ["does not create a Task"]},
        {"id": "root-task-capability", "intent": "capability", "query": "TaskManagement",
         "expected_ids": [NAMESPACE + "installed-task", NAMESPACE + "installed-agent-task"],
         "expected_sources": [".agents/skills/task/SKILL.md", ".agents/skills/agent-task/SKILL.md"]},
        {"id": "root-manager-pair", "intent": "definition", "query": "Sys4AI confirmed Task manager role",
         "expected_ids": [NAMESPACE + "confirmed-task-manager"],
         "expected_sources": ["Roles/task-manager/AGENTS.md", "Roles/task-manager/ROLE.md"], "expected_terms": ["does not establish a live manager"]},
        {"id": "root-director-scope", "intent": "definition", "query": "Sys4AI host Project Director",
         "expected_ids": [NAMESPACE + "host-director"], "expected_sources": ["AGENTS.md", "ROLE.md"], "expected_terms": ["workspace registration"]},
        {"id": "root-ordinary-child", "intent": "definition", "query": "Sys4AI ordinary project sub-agent role",
         "expected_ids": [NAMESPACE + "ordinary-child"], "expected_sources": ["Roles/project-sub-agent/AGENTS.md", "Roles/project-sub-agent/ROLE.md"]},
        {"id": "root-template-derivation", "intent": "relationship", "query": "Registered Sys4AI Template Project",
         "expected_relations": [{"subject": NAMESPACE + "registered-template", "predicate": CORE + "derivesFrom", "object": NAMESPACE + "artifact-template-mapping"}]},
        {"id": "root-child-authority", "intent": "definition", "query": "Registered Sys4AI Template Project",
         "expected_ids": [NAMESPACE + "registered-template"], "expected_sources": ["depot/projects.json"],
         "expected_terms": ["imports no internal vocabulary", "grants no read, write or publication authority"]},
        {"id": "root-memory-publication-scope", "intent": "relationship", "query": "Installed memory skill",
         "expected_relations": [{"subject": NAMESPACE + "installed-memory", "predicate": CORE + "requiresAuthority", "object": memory_authority}]},
        {"id": "root-deprecated-replacement", "intent": "definition", "query": "TaskRequirementDocument",
         "expected_ids": [CORE + "TaskRequirementDocument"], "expected_terms": ["deprecated", CORE + "TRD", "never reassigned"]},
        {"id": "root-current-task-rules", "intent": "current", "query": "Task", "expected_sources": [".agents/skills/task/SKILL.md"], "expected_status": "ok"},
    ]}
    data = encode(competency)
    (output / "competency.json").write_bytes(data)
    manifest["documents"].append({"source": "competency.json", "destination": "ONTOLOGY/modules/project/competency.json",
                                  "sha256": hashlib.sha256(data).hexdigest(), "questions": len(competency["questions"])})
    manifest["sources"] = sorted(sources.values(), key=lambda s: (s["path"], s["locator"]))
    (output / "manifest.json").write_bytes(encode(manifest))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = prepare(args.project_root, args.output)
    print(json.dumps({"project_id": result["project_id"], "documents": result["documents"]}, indent=2))
