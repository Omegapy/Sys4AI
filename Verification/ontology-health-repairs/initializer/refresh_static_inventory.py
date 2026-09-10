"""Rebuild the reviewed initializer inventory during this authorized release only."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "SKILLS-depo/init-new-project"


def main():
    inventory = {"schema_version": 1,
                 "scope": "Complete repaired current starter packages and local contracts; no runtime or project history.",
                 "packages": {}}
    for skill in ("ontology", "memory", "init-new-project"):
        base = ROOT / "SKILLS-depo" / skill
        name = ".agents/skills/" + skill
        inventory["packages"][name] = sorted(name + "/" + path.relative_to(base).as_posix()
            for path in base.rglob("*") if path.is_file() and "__pycache__" not in path.parts
            and path.suffix != ".pyc" and not path.name.startswith("."))
    for collection in ("ONTOLOGY-depo", "MEMORY-depo"):
        base = ROOT / collection
        name = "reference-assets/" + collection
        inventory["packages"][name] = sorted(name + "/" + path.relative_to(base).as_posix()
            for path in base.rglob("*") if path.is_file() and "starter" not in path.relative_to(base).parts
            and "__pycache__" not in path.parts and not path.name.startswith("."))
    inventory["locked_resources"] = {".agents/skills/ontology/" + name:
        hashlib.sha256((ROOT / "SKILLS-depo/ontology" / name).read_bytes()).hexdigest()
        for name in ("requirements-standards.txt", "requirements-semantic.txt",
                     "profiles/standards-v1.json", "profiles/semantic-v1.json")}
    target = PACKAGE / "assets/static-capability-v1.json"
    target.write_text(json.dumps(inventory, indent=2) + "\n")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    helper = PACKAGE / "scripts/init_static_health.py"
    updated, changes = re.subn(r'INVENTORY_SHA256 = "[a-f0-9]+"', 'INVENTORY_SHA256 = "' + digest + '"', helper.read_text())
    assert changes == 1
    helper.write_text(updated)
    print(json.dumps({"inventory_sha256": digest, "required_files": sum(map(len, inventory["packages"].values())),
                      "locked_resources": len(inventory["locked_resources"])}))


if __name__ == "__main__":
    main()
