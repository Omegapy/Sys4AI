"""One-plan, exact-manifest local adoption. Never operates on product projects."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STAGE = HERE / "adoption-stage"
MANIFEST = HERE / "root-adoption-manifest.json"
BASELINE = HERE / "preservation-baseline.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def files(path):
    return sorted(p for p in path.rglob("*") if p.is_file() and not p.is_symlink()
                  and "__pycache__" not in p.parts and p.suffix != ".pyc")


def prepare():
    baseline = json.loads(BASELINE.read_text())["files"]
    entries = []
    desired = {}

    def stage(dest, content, source=None, strategy="copy"):
        target = ROOT / dest
        if target.is_symlink():
            raise RuntimeError("Symlink destination: " + dest)
        before = target.read_bytes() if target.exists() else None
        recorded = baseline.get(dest)
        if recorded and sha(before) != recorded["sha256"]:
            raise RuntimeError("Destination changed since baseline: " + dest)
        if not recorded and before is not None:
            raise RuntimeError("Unreviewed destination appeared: " + dest)
        if before == content:
            return
        staged = STAGE / dest
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_bytes(content)
        desired[dest] = content
        entries.append({"destination": dest, "before_sha256": sha(before) if before is not None else None,
                        "after_sha256": sha(content), "source": source,
                        "source_sha256": sha((ROOT / source).read_bytes()) if source else None,
                        "strategy": strategy, "staged": str(staged.relative_to(ROOT)),
                        "mode": target.stat().st_mode & 0o777 if target.exists() else 0o644})

    def package(source, destination, require_prior_equality=False):
        for p in files(ROOT / source):
            suffix = p.relative_to(ROOT / source).as_posix()
            src, dest = source + "/" + suffix, destination + "/" + suffix
            if require_prior_equality and dest in baseline:
                old_source = baseline.get(src)
                if old_source is None or old_source["sha256"] != baseline[dest]["sha256"]:
                    raise RuntimeError("Customized installed package needs a content merge: " + dest)
            stage(dest, p.read_bytes(), src)

    package("SKILLS-depo/memory", ".agents/skills/memory")
    package("SKILLS-depo/init-new-project", ".agents/skills/init-new-project", True)
    package("Projects/Sys4AI-Template-Project/reference-assets/MEMORY-depo", "reference-assets/MEMORY-depo")
    sections = [
        ("SKILLS-depo/task/SKILL.md", ".agents/skills/task/SKILL.md", "## Optional project memory"),
        ("SKILLS-depo/agent-task/SKILL.md", ".agents/skills/agent-task/SKILL.md", "## Memory evidence references"),
        ("SKILLS-depo/manage-subagent-roles/SKILL.md", ".agents/skills/manage-subagent-roles/SKILL.md", "## Recalled role context"),
        ("SKILLS-depo/agent-task/references/orchestration-contract.md", ".agents/skills/agent-task/references/orchestration-contract.md", "## Optional memory artifacts"),
        ("SKILLS-depo/agent-task/references/task-system-contract.md", ".agents/skills/agent-task/references/task-system-contract.md", "## Memory evidence compatibility"),
        ("ROLES-depo/project-director-ROLE.md", "ROLE.md", "## Project memory responsibility"),
        ("AGENTS-depo/project-template-AGENTS.md", "AGENTS.md", "## Project memory"),
        ("ROLES-depo/task-manager-AGENTS.md", "Roles/task-manager/AGENTS.md", "## Project memory inputs"),
        ("ROLES-depo/task-manager-ROLE.md", "Roles/task-manager/ROLE.md", "## Memory selection and capture"),
        ("ROLES-depo/project-sub-agent-AGENTS.md", "Roles/project-sub-agent/AGENTS.md", "## Memory within an assignment"),
        ("ROLES-depo/project-sub-agent-ROLE.md", "Roles/project-sub-agent/ROLE.md", "## Memory result boundary"),
        ("SPECS-depo/project-template.gitignore", ".gitignore", "# Project memory: only classified local runtime products are excluded."),
    ]
    for source, dest, heading in sections:
        current = (ROOT / dest).read_text()
        if heading in current:
            raise RuntimeError("Adoption section already exists: " + dest)
        source_text = (ROOT / source).read_text()
        extension = source_text[source_text.index(heading):]
        stage(dest, (current.rstrip() + "\n\n" + extension).encode(), source, "append-only bounded merge")
    src = "SKILLS-depo/task/references/memory-context.md"
    stage(".agents/skills/task/references/memory-context.md", (ROOT / src).read_bytes(), src)
    src = "MEMORY-depo/starter/MEMORY/README.md"
    stage("MEMORY/README.md", (ROOT / src).read_bytes(), src)
    stage("requirements-memory.txt", b"# Root optional PDF extraction; the backend pilot owns its separate runtime.\n-r .agents/skills/memory/requirements-extraction.txt\n", strategy="root dependency declaration")
    specs = """\n\n## Project memory\n\nThe root owns portable Markdown records in `MEMORY/` and its `memory.yaml`\nconfiguration under identity `sys4ai-depot`. Adopted contracts live at\n`reference-assets/MEMORY-depo/`; reusable sources remain in `MEMORY-depo/` and\n`SKILLS-depo/memory/`. General retrieval permits README, docs and research; it\nexcludes child projects, Tasks, roles, reusable assets and private/runtime paths.\n\nThe memory core and Task/role integration retain Python 3.12 standard-library\nindependence. Configuration/frontmatter use a documented JSON subset of YAML.\n`requirements-memory.txt` declares the existing optional PyMuPDF extraction\ndependency. The pinned Basic Memory pilot uses `.venv-memory-pilot` and the\nmemory skill's separate backend requirements/profile; the root `.venv` is\npreserved. Setup and ordinary reads provision no packages, models or services.\n\nThe [state-path contract](./.agents/skills/memory/references/state-paths.md)\nseparates derived products from durable backend configuration and maintenance\nrecovery. The [integration contract](./.agents/skills/memory/references/task-integration.md)\nuses existing Task artifacts and inputs without a schema change. Initializer\nedition `governance-starter-v5` supplies empty project memory; v1-v4 receipts,\nroot intake/closure policy and existing product content retain their semantics.\nSemantic use is controlled by current configuration and the exact local pilot\ncertification. Inspect `memory.py --project-root . health` for current readiness.\n"""
    stage("SPECS.md", (ROOT.joinpath("SPECS.md").read_text().rstrip() + specs).encode(), strategy="root-specific memory specification")
    readme = """\n\n## Project memory\n\nThe [memory skill](./.agents/skills/memory/SKILL.md) provides project-owned\n[canonical records](./MEMORY/README.md), exact source retrieval and a guarded\nlocal Basic Memory adapter. [Configuration](./memory.yaml) and the\n[release assessment](./Verification/project-memory/RELEASE-ASSESSMENT.md) record\nthe current scope and verification. Recalled conclusions remain evidence;\ncurrent instructions, Tasks, role pairs and original sources retain authority.\n\nUse `.venv/bin/python .agents/skills/memory/scripts/memory.py --project-root .\nsearch 'query'` for lookup, or replace the search arguments with `health` for\ncurrent readiness. Reads perform no maintenance or provisioning. Canonical\npublication needs the exact current Director/manager grant. New projects receive\nonly the empty Template capability; existing products require their own adoption.\n"""
    stage("README.md", (ROOT.joinpath("README.md").read_text().rstrip() + readme).encode(), strategy="root-specific memory navigation")
    source = "MEMORY-depo/starter/memory.yaml"
    config = json.loads((ROOT / source).read_text())
    config["project"] = {"id": "sys4ai-depot", "name": "Sys4AI Depot", "root": "."}
    config["publication"]["director"] = {"actor_id": "/root", "scope": ["MEMORY", "Verification/project-memory",
        *[config["state"][k] for k in ("projection", "normalized", "index", "backend_config", "maintenance")]],
        "authority": [{"path": p, "sha256": sha(desired.get(p, (ROOT / p).read_bytes()))} for p in ("SOUL.md", "AGENTS.md", "ROLE.md")]}
    stage("memory.yaml", (json.dumps(config, indent=2, sort_keys=True) + "\n").encode(), source, "root identity and scoped Director specialization; backend disabled")
    result = {"schema_version": 1, "root": str(ROOT), "plan_id": "PLAN-20260908-5F47ADB2", "entries": entries,
              "generated_after_copy": {"path": "Roles/INDEX.md", "before_sha256": baseline["Roles/INDEX.md"]["sha256"],
                  "operation": ".agents/skills/manage-subagent-roles/scripts/role_catalog.py reindex"}}
    MANIFEST.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"files": len(entries), "manifest": str(MANIFEST), "sha256": sha(MANIFEST.read_bytes())}))


def apply(expected):
    raw = MANIFEST.read_bytes()
    if sha(raw) != expected:
        raise RuntimeError("Adoption manifest differs from reviewed digest.")
    manifest = json.loads(raw)
    if manifest["root"] != str(ROOT):
        raise RuntimeError("Adoption belongs to another root.")
    # Validate the whole exact manifest before the first destination write.
    for item in manifest["entries"]:
        dest = ROOT / item["destination"]
        if dest.is_symlink() or any(p.is_symlink() for p in dest.parents if p != ROOT and p.is_relative_to(ROOT)):
            raise RuntimeError("Unsafe adoption destination.")
        current = sha(dest.read_bytes()) if dest.exists() else None
        if current not in (item["before_sha256"], item["after_sha256"]):
            raise RuntimeError("Destination changed: " + item["destination"])
        if sha((ROOT / item["staged"]).read_bytes()) != item["after_sha256"]:
            raise RuntimeError("Staged adoption changed.")
        if item["source"] and sha((ROOT / item["source"]).read_bytes()) != item["source_sha256"]:
            raise RuntimeError("Source changed since adoption review: " + item["source"])
    applied = []
    for item in manifest["entries"]:
        dest = ROOT / item["destination"]
        if dest.exists() and sha(dest.read_bytes()) == item["after_sha256"]:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as stream:
            stream.write((ROOT / item["staged"]).read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
            temp = Path(stream.name)
        os.chmod(temp, item["mode"])
        if (sha(dest.read_bytes()) if dest.exists() else None) != item["before_sha256"]:
            temp.unlink()
            raise RuntimeError("Destination changed before atomic replacement.")
        os.replace(temp, dest)
        applied.append(item["destination"])
    receipt = {"manifest_sha256": expected, "applied": applied, "files": len(manifest["entries"]),
               "status": "copied", "role_index": "requires existing helper reindex"}
    (HERE / "root-adoption-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "apply"))
    parser.add_argument("--expected-manifest-sha256")
    args = parser.parse_args()
    prepare() if args.operation == "prepare" else apply(args.expected_manifest_sha256)
