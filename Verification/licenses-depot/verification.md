# Licensing depot verification

Completed locally on 2026-09-08 against the
[implementation requirements and plan](../../Implementation_Plans/licenses_depot_implementation_plan_2026-09-08.md).

## Requirement acceptance

| Requirement | Result | Current evidence |
| --- | --- | --- |
| LIC-001 | Passed | `LICENSES-depo` contains the routing notice and complete Apache 2.0 / CC BY 4.0 companions. [Source records](sources.json) identify the unchanged supplied files and exact publisher-body hashes. |
| LIC-002 | Passed | The root license trio equals its source bytes. [Root adoption](root-adoption.json) records exact file hashes and the bounded initializer adoption. Root navigation and specifications expose the system. |
| LIC-003 | Passed | [Template status](template-status.json) reports 87 managed files, current, with no conflicts. [Watcher status](watcher-status.json) has a fresh successful check from its current PID. The three Template root files equal the source and active root. |
| LIC-004 | Passed | [CLI evidence](cli-verification.json) records seven successful workflows using actual installed-helper and live-Template copies. Both creation and unlicensed preparation receive the trio; existing file/directory license systems are preserved. All saved CLI receipts were reopened. |
| LIC-005 | Passed | Source tests exercise v1/v2/v3 recovery and reruns under the original contracts; v4 records licensing independently. The original examples and live registry retain their hashes. Pre-existing edits and historical adoption receipts were retained. No product project, Task ledger, or managed TRD was changed; no dependency was installed and no Git commit or publication was performed. |

## Tests and review

| Check | Observed result |
| --- | --- |
| [Source initializer suite](initializer-tests.log), `.venv/bin/python -m unittest discover -s SKILLS-depo/init-new-project/tests -v` | 55 run: 54 passed, 1 skipped. Includes nine licensing tests. |
| [Updater suite](template-update-tests.log), `.venv/bin/python -m unittest discover -s tests -p test_template_update.py -v` | 48 run: 47 passed, 1 skipped. Includes source mappings, update propagation, and protected project/root sentinels. |
| [Root contract suite](root-contract-tests.log), `.venv/bin/python -m unittest discover -s tests -p test_repository_contract.py -v` | 15 passed. |
| [Template contracts](template-contract-tests.log), root Python interpreter with `-m unittest discover -s tests -v` from the Template | 8 passed. |
| Actual installed CLI workflows in a disposable depot, with `Python -I -S` | 7 passed; create, prepare, reruns, alternate marker and license-directory preservation. Original live source hashes matched all receipt inputs. |
| Source/root/Template comparisons | Complete initializer package and all three licenses match; legal-code bodies match the publisher bytes. |
| Final patch check | `git diff --check` passed. |

The two skipped tests require distinct case-equivalent directories, which this
case-insensitive filesystem cannot create. Existing case-safety tests still ran.

The native `project-sub-agent` independently reviewed the initializer and ran
all nine licensing tests. Review found and verified fixes for a `LICENSE/`
directory collision and a hardlinked alternate marker being rejected too late.
It reported no remaining mandatory defects. The final reviewed initializer
SHA-256 is `1bb13eeccdf830c271fec39bbb0e0fb7be41040bc63d0c56f2e3fe516bcc269d`.
The role pair digests matched the fresh filesystem catalog; no model or
reasoning overrides were used and the review made no workspace changes.

The supplementary personal skill-creator `quick_validate.py` could not start
because PyYAML is absent from both the project and bundled runtimes. No package
was installed. The existing updater and Template contract validators passed
their skill metadata, Python, JSON, package and local-link checks.

## Reverse artifact coverage and boundaries

The [changed-file manifest](changed-files.json) records exact pre-turn and final
hashes. Licensing source files and their root copies implement LIC-001/002.
Mappings, Template copies, and template documentation implement LIC-003.
Initializer source, active copies, policy, receipt schema, and tests implement
LIC-004/005. Root/depot guidance, this packet, and the plan provide traceability
for LIC-001 through LIC-005. Existing historical receipts were retained; the new
adoption record identifies the current package without rewriting old evidence.

The highest verification reached is end-to-end initialization in disposable
depots using copies of the actual live assets, plus observed live Template
publication and watcher readiness. No real product was created or relicensed,
and no Git commit, push, publication, dependency installation, reboot, or
drive-disconnection recovery was performed. Licensing embedded only in unrelated
prose or package metadata still needs the project review required by the skill.
This verification establishes implementation behavior, not legal enforceability.
