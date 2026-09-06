"""Explicitly enabled immutable-wheel checks in a disposable Sys4AI depot."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from test_initializer import (
    BASELINE,
    SOURCE_DEPOT,
    fixture_depot,
    load_helper,
    manifest,
)


def run(arguments, cwd):
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.update(
        PYTHONDONTWRITEBYTECODE="1",
        GIT_OPTIONAL_LOCKS="0",
        UV_NO_CACHE="1",
        UV_PYTHON_DOWNLOADS="never",
        TMPDIR="/private/tmp",
    )
    result = subprocess.run(
        arguments,
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        timeout=600,
        check=False,
    )
    if result.returncode:
        raise AssertionError(
            {
                "returncode": result.returncode,
                "program": Path(arguments[0]).name,
                "stdout": result.stdout[-1200:],
                "stderr_characters": len(result.stderr),
            }
        )
    return json.loads(result.stdout)


@unittest.skipUnless(
    os.environ.get("SYS4AI_INITIALIZER_ARTIFACT"),
    "set SYS4AI_INITIALIZER_ARTIFACT to authorize disposable build and installations",
)
class InstalledWheelTests(unittest.TestCase):
    def test_creation_manual_route_recovery_and_equivalent_rerun(self):
        live_registry_before = (SOURCE_DEPOT / "depot/projects.json").read_bytes()
        live_children_before = sorted(
            path.name for path in (SOURCE_DEPOT / "Projects").iterdir()
        )
        source_receipt = Path(os.environ["SYS4AI_INITIALIZER_ARTIFACT"])
        source_artifact = json.loads(source_receipt.read_text())
        source_product = Path(source_artifact["source_root"])
        self.assertEqual(
            SOURCE_DEPOT / "Projects/Sys4AI-Memory-Service", source_product
        )
        run(
            [
                sys.executable,
                str(source_product / "tools/build_consumer_artifact.py"),
                "verify",
                str(source_receipt),
            ],
            SOURCE_DEPOT,
        )
        with tempfile.TemporaryDirectory(
            prefix="sys4ai-initializer-e2e-", dir="/private/tmp"
        ) as temporary:
            root = fixture_depot(Path(temporary))
            helper = load_helper(root / "SKILLS-depo/init-new-project")
            product = root / "Projects/Sys4AI-Memory-Service"
            # Rebuild the same source snapshot inside the fixture, so its own
            # truthful build receipt has a fixture source root. No receipt fields
            # are rewritten to masquerade as another build.
            with zipfile.ZipFile(
                source_receipt.parent / source_artifact["wheel"]["filename"]
            ) as package:
                for relative, expected in source_artifact["source_manifest"].items():
                    raw = (
                        package.read(relative.removeprefix("src/"))
                        if relative.startswith("src/")
                        else (source_product / relative).read_bytes()
                    )
                    self.assertEqual(
                        expected, hashlib.sha256(raw).hexdigest(), relative
                    )
                    target = product / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
            built = run(
                [
                    sys.executable,
                    str(product / "tools/build_consumer_artifact.py"),
                    "build",
                    "--project-root",
                    str(product),
                    "--python",
                    sys.executable,
                ],
                product,
            )
            artifact_path = Path(built["artifact_receipt"])
            artifact = json.loads(artifact_path.read_text())
            self.assertEqual(
                source_artifact["wheel"]["sha256"], artifact["wheel"]["sha256"]
            )
            evidence = {
                "source_artifact_receipt": str(source_receipt),
                "fixture_artifact": str(artifact_path),
                "wheel_sha256": artifact["wheel"]["sha256"],
                "cases": [],
            }
            arguments = {
                "mode": "create",
                "destination": root / "Projects/Orchard",
                "project_id": "orchard",
                "project_name": "Orchard",
                "purpose": "Track ORCHARD_FIXTURE_MARKER observations.",
                "principal_id": "fixture-owner",
                "artifact_receipt": artifact_path,
            }
            command = [
                sys.executable,
                str(root / "SKILLS-depo/init-new-project/scripts/init_new_project.py"),
                "create",
                "--destination",
                str(arguments["destination"]),
                "--project-id",
                arguments["project_id"],
                "--project-name",
                arguments["project_name"],
                "--purpose",
                arguments["purpose"],
                "--principal-id",
                arguments["principal_id"],
                "--artifact-receipt",
                str(artifact_path),
            ]
            canonical = run(command, root)
            self.assertEqual("completed", canonical["status"])
            self.assertGreater(
                canonical["functional_memory"]["exact_recall_result_count"], 0
            )
            self.assertEqual(
                artifact["wheel"]["sha256"], canonical["runtime"]["wheel_sha256"]
            )
            self.assertTrue(
                Path(canonical["runtime"]["observed"]["origin"]).is_relative_to(
                    arguments["destination"] / ".venv"
                )
            )
            self.assertFalse(canonical["runtime"]["observed"]["provider_imported"])
            self.assertFalse(canonical["initialization"]["provider_initialized"])
            self.assertNotIn(
                "cognee",
                {
                    name.casefold()
                    for name in canonical["runtime"]["observed"]["dependencies"]
                },
            )
            self.assertTrue((arguments["destination"] / helper.FINAL_RECEIPT).is_file())
            for forbidden in (".git", ".gitmodules", "models", "src/sys4ai_memory"):
                self.assertFalse((arguments["destination"] / forbidden).exists())
            # Rerun keeps every file byte and path, including derived receipts.
            before = manifest(arguments["destination"])
            before_registry = (root / "depot/projects.json").read_bytes()
            source = root / "SKILLS-depo/communication/SKILL.md"
            source.write_text(
                source.read_text() + "\nA later depot edit is not auto-adopted.\n"
            )
            repeated = run(command, root)
            self.assertEqual("verified-existing", repeated["rerun"])
            self.assertEqual(before, manifest(arguments["destination"]))
            self.assertEqual(
                before_registry, (root / "depot/projects.json").read_bytes()
            )
            evidence["cases"].append(
                {
                    "case": "canonical-installed-cli-and-equivalent-rerun",
                    "receipt": canonical,
                    "file_manifest": before,
                }
            )

            manual = root / "Projects/ManualOrchard"
            shutil.copytree(root / "Projects/Sys4AI-Template-Project", manual)
            (manual / "field-notes.txt").write_text(
                "Unrelated manual-copy notes stay intact.\n"
            )
            manual_args = {
                **arguments,
                "mode": "prepare-existing",
                "destination": manual,
                "project_id": "manual-orchard",
                "project_name": "Manual Orchard",
                "purpose": "Track MANUAL_ORCHARD_MARKER observations.",
            }
            prepared = helper.run_initialization(**manual_args)
            self.assertEqual("prepared", prepared["status"])
            self.assertFalse((manual / ".sys4ai").exists())
            self.assertEqual(
                source.read_bytes(),
                (manual / ".agents/skills/communication/SKILL.md").read_bytes(),
            )
            initial = run(prepared["next_command"], manual)
            self.assertTrue(
                initial["result"]["initialization"]["exact_index_initialized"]
            )
            run(
                helper.memory_arguments(
                    manual,
                    prepared["identity"],
                    "sync",
                    "--idempotency-key",
                    "manual-exact-sync",
                ),
                manual,
            )
            recalled = run(
                helper.memory_arguments(
                    manual,
                    prepared["identity"],
                    "recall",
                    "MANUAL_ORCHARD_MARKER",
                    "--mode",
                    "exact",
                ),
                manual,
            )
            self.assertTrue(recalled["result"]["retrieval"]["results"])
            foreign = run(
                helper.memory_arguments(
                    manual,
                    prepared["identity"],
                    "recall",
                    "ORCHARD_FIXTURE_MARKER",
                    "--mode",
                    "exact",
                ),
                manual,
            )
            self.assertFalse(foreign["result"]["retrieval"]["results"])
            self.assertEqual(
                "Unrelated manual-copy notes stay intact.\n",
                (manual / "field-notes.txt").read_text(),
            )
            manual_before = manifest(manual)
            manual_repeated = helper.run_initialization(**manual_args)
            self.assertEqual("verified-existing", manual_repeated["rerun"])
            self.assertEqual(manual_before, manifest(manual))
            evidence["cases"].append(
                {
                    "case": "shared-manual-preparation-direct-init-and-isolation",
                    "receipt": prepared,
                    "initialization": initial["result"]["initialization"],
                    "exact_result_count": len(
                        recalled["result"]["retrieval"]["results"]
                    ),
                    "foreign_result_count": 0,
                    "file_manifest": manual_before,
                }
            )

            recovery_args = {
                **arguments,
                "destination": root / "Projects/Recovery",
                "project_id": "recovery",
                "project_name": "Recovery",
            }
            original_process = helper.process

            def lose_preparation_result(argv, cwd, **kwargs):
                result = original_process(argv, cwd, **kwargs)
                if "sys4ai_memory.bootstrap" in argv:
                    raise helper.InitializationError(
                        "injected interruption after common preparation"
                    )
                return result

            with (
                patch.object(helper, "process", side_effect=lose_preparation_result),
                self.assertRaises(helper.InitializationError) as preparation_failed,
            ):
                helper.run_initialization(**recovery_args)
            self.assertEqual(
                "memory-preparation",
                preparation_failed.exception.report["recovery"]["stage"],
            )

            def fail_initialization(argv, cwd, **kwargs):
                if "init-memory" in argv:
                    raise helper.InitializationError(
                        "injected direct initialization failure"
                    )
                return original_process(argv, cwd, **kwargs)

            with (
                patch.object(helper, "process", side_effect=fail_initialization),
                self.assertRaises(helper.InitializationError) as failed,
            ):
                helper.run_initialization(**recovery_args)
            self.assertEqual(
                "memory-initialization", failed.exception.report["recovery"]["stage"]
            )
            (recovery_args["destination"] / "unrelated.txt").write_text(
                "preserve through bootstrap recovery"
            )
            recovered = helper.run_initialization(**recovery_args)
            self.assertEqual("completed", recovered["status"])
            self.assertEqual(
                "preserve through bootstrap recovery",
                (recovery_args["destination"] / "unrelated.txt").read_text(),
            )
            evidence["cases"].append(
                {
                    "case": "preparation-interruption-and-direct-bootstrap-failure-owned-resume",
                    "preparation_failure": preparation_failed.exception.report[
                        "recovery"
                    ],
                    "failure": failed.exception.report["recovery"],
                    "receipt": recovered,
                }
            )

            # Validate each adopted package in the actual consumer. The static
            # packages have no executable suite; all Python resources were parsed
            # and their exact package bytes were verified by the initializer.
            package_checks = []
            for name in BASELINE:
                suite = arguments["destination"] / ".agents/skills" / name / "tests"
                helper.package_files(arguments["destination"] / ".agents/skills" / name)
                if not suite.exists() or name == "task":
                    package_checks.append(
                        {
                            "skill": name,
                            "check": "metadata and exact source bytes",
                            "status": "passed",
                        }
                    )
                    if name == "task":
                        package_checks[-1]["source_only_suite"] = (
                            "test_task_project_director_orchestration.py requires the producer depot's SKILLS-depo, ROLES-depo and Verification; it is not a consumer test route"
                        )
                    continue
                selection = (
                    ["test_role_catalog.RoleCatalogTests"]
                    if name == "manage-subagent-roles"
                    else ["discover", "-s", str(suite)]
                )
                result = subprocess.run(
                    [
                        str(arguments["destination"] / ".venv/bin/python"),
                        "-m",
                        "unittest",
                        *selection,
                    ],
                    cwd=suite
                    if name == "manage-subagent-roles"
                    else arguments["destination"],
                    env={
                        **os.environ,
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "GIT_OPTIONAL_LOCKS": "0",
                        "TMPDIR": "/private/tmp",
                    },
                    capture_output=True,
                    text=True,
                    timeout=180,
                    check=False,
                )
                self.assertEqual(
                    0,
                    result.returncode,
                    {"skill": name, "stderr": result.stderr[-2000:]},
                )
                package_checks.append(
                    {
                        "skill": name,
                        "status": "passed",
                        "selection": selection,
                        "result": result.stderr.splitlines()[-4:],
                    }
                )
                if name == "manage-subagent-roles":
                    package_checks[-1]["source_contract_limit"] = (
                        "The unchanged producer ImplementationContractTests expects an obsolete exact ROLE heading; portable RoleCatalogTests exercise actual consumer role operations"
                    )
            evidence["package_checks"] = package_checks
            schema = (
                root
                / "SKILLS-depo/init-new-project/assets/initialization-receipt.schema.json"
            )
            for case in evidence["cases"]:
                payload = root / "receipt-under-test.json"
                payload.write_text(json.dumps(case["receipt"]))
                run(
                    [
                        str(
                            SOURCE_DEPOT
                            / "Projects/Sys4AI-Memory-Service/.venv/bin/python"
                        ),
                        "-I",
                        "-c",
                        "import json,jsonschema,sys;jsonschema.validate(json.load(open(sys.argv[1])),json.load(open(sys.argv[2])));print('{}')",
                        str(payload),
                        str(schema),
                    ],
                    root,
                )
            for case in evidence["cases"]:
                rendered = json.dumps(case["receipt"])
                self.assertNotIn('"preview', rendered)
                self.assertNotIn('"impact_digest"', rendered)
                self.assertNotIn(str(Path.home()), rendered)
            self.assertFalse(
                (root / "Projects/Sys4AI-Template-Project/.sys4ai").exists()
            )
            self.assertFalse((product / ".sys4ai").exists())
            self.assertEqual(
                live_registry_before,
                (SOURCE_DEPOT / "depot/projects.json").read_bytes(),
            )
            self.assertEqual(
                live_children_before,
                sorted(path.name for path in (SOURCE_DEPOT / "Projects").iterdir()),
            )
            evidence["live_registry_and_projects_inventory_unchanged"] = True
            selected = os.environ.get("SYS4AI_INITIALIZER_EVIDENCE_DIR")
            if selected:
                output = Path(selected)
                self.assertTrue(
                    output.is_absolute()
                    and output.is_relative_to(Path("/private/tmp"))
                    and output.is_dir()
                    and not output.is_symlink()
                )
                (output / "initializer-e2e-evidence.json").write_text(
                    json.dumps(evidence, indent=2, sort_keys=True) + "\n"
                )


if __name__ == "__main__":
    unittest.main()
