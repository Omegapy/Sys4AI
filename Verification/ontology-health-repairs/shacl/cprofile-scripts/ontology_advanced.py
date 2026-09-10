"""Strict companion and exact selected semantic extensions; no provisioning."""
from pathlib import Path
import re
from ontology_core import (CORE, OntologyError, canonical_bytes, decode_json, digest,
                           exact, load_config, read_bytes, require, safe_path, sha256,
                           source_status)
from ontology_limits import limits

VERSION = "2.0.0"
CONFIG = "ontology-advanced.yaml"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
AXIOMS = {RDF+"type", RDFS+"subClassOf", RDFS+"subPropertyOf", OWL+"equivalentClass",
          OWL+"equivalentProperty", OWL+"sameAs", OWL+"differentFrom", OWL+"inverseOf",
          OWL+"disjointWith", OWL+"propertyDisjointWith"}
IRI = re.compile(r"(?:urn:|https?://)[^\s<>\"{}|^`\\]+\Z")


def iri(value):
    require(isinstance(value, str) and len(value) <= 2000 and IRI.fullmatch(value), "invalid_iri", "Expected a bounded absolute IRI.")
    return value


def term(value, *, literal=True, blank=False):
    if isinstance(value, str): return iri(value)
    if blank and isinstance(value, dict) and set(value) == {"bnode"}:
        require(isinstance(value["bnode"], str) and re.fullmatch(r"[A-Za-z0-9_-]{1,120}", value["bnode"]), "invalid_term", "Invalid blank node identity.")
        return value
    require(literal, "invalid_term", "Expected a named resource.")
    exact(value, ("value",), ("datatype", "language"))
    require(isinstance(value["value"], str) and len(value["value"].encode()) <= 100000, "invalid_literal", "Expected a bounded literal string.")
    require(not ("datatype" in value and "language" in value), "invalid_literal", "A literal cannot have both datatype and language.")
    if "datatype" in value: iri(value["datatype"])
    if "language" in value:
        require(isinstance(value["language"], str) and re.fullmatch(r"[a-zA-Z]+(?:-[a-zA-Z0-9]+)*", value["language"]), "invalid_literal", "Invalid language tag.")
    return value


def load_advanced(root, required=False, _overrides=None):
    overrides = _overrides or {}
    path = safe_path(root, CONFIG, must_exist=False)
    if not path.exists() and CONFIG not in overrides:
        require(not required, "advanced_absent", "The selected project has no advanced companion.")
        return None
    cfg = decode_json(overrides[CONFIG] if CONFIG in overrides else read_bytes(path), path=CONFIG)
    exact(cfg, ("schema_version", "profiles", "extensions", "limits"), ("project_id", "publication"))
    require(type(cfg["schema_version"]) is int and cfg["schema_version"] == 1, "unsupported_advanced_version", "Unsupported advanced companion version.")
    core = load_config(root)
    require(cfg.get("project_id", core["project"]["id"]) == core["project"]["id"], "identity_mismatch", "Advanced companion belongs to a different project.")
    exact(cfg["profiles"], (), ("standards", "inference", "semantic", "guards", "workbench"))
    for name, profile in cfg["profiles"].items():
        require(isinstance(profile, dict) and type(profile.get("enabled")) is bool, "invalid_profile", "Profile must declare enabled as a Boolean.")
        if name == "standards":
            exact(profile, ("enabled",), ("python", "certification"))
            require(profile.get("python", ".venv-ontology-standards/bin/python") == ".venv-ontology-standards/bin/python", "invalid_profile", "Standards uses its own selected project environment.")
            if "certification" in profile: safe_path(root, profile["certification"], must_exist=False)
        elif name == "inference": exact(profile, ("enabled",))
        elif name == "semantic":
            exact(profile, ("enabled",), ("python", "model_manifest"))
            require(profile.get("python", ".venv-ontology-semantic/bin/python") == ".venv-ontology-semantic/bin/python", "invalid_profile", "Semantic uses its selected independent environment.")
            require(profile.get("model_manifest", ".sys4ai/ontology/semantic/model.json") == ".sys4ai/ontology/semantic/model.json", "invalid_profile", "Unsupported semantic model manifest path.")
        elif name == "guards":
            exact(profile, ("enabled",), ("contract", "adapters", "bootstrap"))
            for key in ("contract", "adapters", "bootstrap"):
                if key in profile:
                    exact(profile[key], ("path", "sha256")); digest(profile[key]["sha256"])
                    safe_path(root, profile[key]["path"], must_exist=False)
        elif name == "workbench":
            exact(profile, ("enabled",), ("host", "port", "session_seconds", "max_request_bytes"))
            require(profile.get("host", "127.0.0.1") == "127.0.0.1", "invalid_profile", "Workbench binds only IPv4 loopback.")
            for key, low, high, default in (("port", 0, 65535, 0), ("session_seconds", 60, 3600, 900), ("max_request_bytes", 1024, 1000000, 1000000)):
                require(type(profile.get(key, default)) is int and low <= profile.get(key, default) <= high, "invalid_profile", "Invalid workbench budget: " + key)
    require(isinstance(cfg["extensions"], list) and len(cfg["extensions"]) <= 100, "invalid_extensions", "Extensions require a bounded exact selection.")
    seen = set()
    for ref in cfg["extensions"]:
        exact(ref, ("path", "sha256")); digest(ref["sha256"])
        require(ref["path"].startswith("ONTOLOGY/extensions/") and ref["path"].endswith(".json") and ref["path"] not in seen, "extension_scope", "Extension must be a unique selected JSON file under ONTOLOGY/extensions.")
        safe_path(root, ref["path"], must_exist=ref["path"] not in overrides); seen.add(ref["path"])
    limits(cfg["limits"])
    if "publication" in cfg:
        publication=cfg['publication']; exact(publication,('enabled','binding'))
        require(type(publication['enabled']) is bool,'invalid_publication','Advanced publication enabled must be Boolean.')
        binding=publication['binding']
        if binding is not None:
            exact(binding,('actor_id','scope','authority'))
            require(isinstance(binding['actor_id'],str) and binding['actor_id'],'invalid_publication','Advanced publication requires a destination-local actor.')
            require(isinstance(binding['scope'],list) and set(binding['scope'])=={'ontology-advanced.yaml','ONTOLOGY/extensions'} and len(binding['scope'])==2,'invalid_publication','Advanced publication selects only extension data and their companion locks.')
            refs=binding['authority']
            require(isinstance(refs,list) and len(refs)==3 and {r.get('path') for r in refs if isinstance(r,dict)}=={'SOUL.md','AGENTS.md','ROLE.md'},'invalid_publication','Advanced authority binds the exact governing trio.')
            for ref in refs: exact(ref,('path','sha256')); digest(ref['sha256'])
        require(not publication['enabled'] or binding is not None,'invalid_publication','Enabled advanced publication requires an explicit local binding.')
    return cfg


def load_extensions(project, cfg, _overrides=None):
    overrides = _overrides or {}
    extensions, inputs, sources, ids = [], {}, [], set(project.by_id)
    for ref in cfg["extensions"]:
        data = overrides[ref["path"]] if ref["path"] in overrides else read_bytes(safe_path(project.root, ref["path"]))
        require(sha256(data) == ref["sha256"], "extension_changed", "Selected extension differs from its exact lock.", path=ref["path"])
        ext = decode_json(data, path=ref["path"])
        exact(ext, ("schema_version", "id", "version", "project_id", "axioms", "annotations", "negative_assertions"), ("shapes",))
        require(type(ext["schema_version"]) is int and ext["schema_version"] == 1, "unsupported_extension_version", "Unsupported extension version.")
        require(ext["project_id"] == project.project_id, "identity_mismatch", "Extension belongs to a different project.")
        require(isinstance(ext["version"], str) and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", ext["version"]), "invalid_extension", "Extension requires a semantic version.")
        require(isinstance(ext["id"], str) and ext["id"].startswith(project.namespace) and ext["id"] not in ids, "duplicate_id", "Extension identity must be unique in its project.")
        ids.add(ext["id"])
        for field in ("axioms", "annotations", "negative_assertions"):
            require(isinstance(ext[field], list) and len(ext[field]) <= 10000, "invalid_extension", "Extension statements require a bounded array.")
            for statement in ext[field]:
                exact(statement, ("id", "subject", "predicate", "object", "sources"))
                require(isinstance(statement["id"],str) and statement["id"].startswith(project.namespace) and statement["id"] not in ids, "duplicate_id", "Statement must have a unique project identity.")
                ids.add(statement["id"]); iri(statement["subject"]); iri(statement["predicate"]); term(statement["object"])
                if field == "axioms":
                    require(statement["predicate"] in AXIOMS or statement["predicate"].startswith(project.namespace), "unsupported_axiom", "Axiom is outside the finite profile.")
                    require(not statement["subject"].startswith(CORE), "core_redefinition", "Project extensions cannot redefine locked core semantics.")
                elif field == "annotations":
                    require(statement['predicate'] not in AXIOMS and not statement['predicate'].startswith(OWL),'unsupported_annotation','Formal axioms must use the approved axiom channel.')
                require(isinstance(statement["sources"], list) and statement["sources"], "missing_provenance", "Approved extensions require exact selected sources.")
                for source in statement["sources"]: sources.append(source_status(project, source))
        require(isinstance(ext.get('shapes',[]),list) and len(ext.get('shapes',[]))<=100,'invalid_extension','Shapes require a bounded selected list.')
        for shape in ext.get("shapes", []):
            exact(shape, ("path", "sha256")); digest(shape["sha256"])
            require(shape["path"].startswith("ONTOLOGY/extensions/") and shape["path"].endswith(".ttl"), "extension_scope", "Shapes must be selected local Turtle files.")
            data = overrides[shape["path"]] if shape["path"] in overrides else read_bytes(safe_path(project.root, shape["path"]))
            require(sha256(data) == shape["sha256"], "extension_changed", "Shape lock changed.")
            inputs[shape["path"]] = shape["sha256"]
        inputs[ref["path"]] = ref["sha256"]
        extensions.append(ext)
    return extensions, inputs, sources
