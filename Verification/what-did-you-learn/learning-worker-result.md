# Learning workflow worker result

The assigned source work for PLAN-20260909-2AB7D4CC TASK-003 through TASK-006
is implemented. The parent directly accepted those source contracts before
this worker completed its focused TASK-016 test additions. The initial six
relevant suites passed 47 tests; the optional-companion discovery correction
and its current results are recorded below. This result does not accept the whole plan,
record Task state, claim installed adoption or substitute for native scenarios.

## Input and authority receipts

- Assigned role: `Roles/project-sub-agent/AGENTS.md`, SHA256
  `7d064ae5d5954af65fc1a83b2ce1c69562d5c31f085e70ac92c3ad0bf2e7eec2`;
  `Roles/project-sub-agent/ROLE.md`, SHA256
  `4c3ac5415030ab770d9af7b73fc773da43d07b041889c77a8755974284c874e2`.
- Read `SOUL.md`, SHA256
  `3aa4841fa9f2dc177beabaebd341368d797d224cce3bb18b3fd494f34fa473b2`,
  root ROLE/SPECS, and the communication skill. The full-history assignment
  inherited the parent's exact model/effort without overrides; no children
  were launched by this worker.
- Initial canonical plan input: revision 4, SHA256
  `e13ccaa11e6f65dfb04d7671f9e5e733020a161acd0738605af4d7a4ed2533c8`.
  The parent subsequently supplied phase-entry approval, the acceptance matrix
  and metadata progression through revision 23. This worker made no canonical
  plan, Task, TRD or role-index mutation.
- Read the approved TRD revision 2, SHA256
  `bb587df74695cff40c1fbe6a43c5e74951f1b90573992f6e70f744ee16cef061`,
  and the original handoff, SHA256
  `9651eb78b0c54f6232273148970030dff29aa734b3ef9216a746729d67f21604`.
  Existing memory policies, helpers and tests supplied the actual interface.
- Source/adoption boundary and protected baseline are the parent's
  [baseline](baseline.json), [adoption manifest](adoption-manifest.json),
  [acceptance matrix](acceptance-matrix.json) and [scenario protocol](scenario-protocol.md).

## Delivered artifacts

[learning-source-manifest.json](learning-source-manifest.json) records exact
current SHA256 values and sizes for all 17 authored source files.

| Work | Exact source artifacts | Result |
| --- | --- | --- |
| TASK-003 | `LEARNING-depo/README.md`, `policy.md`, `review-contract.md`, `contract.json`, `assets/lesson-body-template.md` | Substantive 1.0.0 module, eight-step review, body-only lesson assets and a neutral capability manifest. |
| TASK-004 | `SKILLS-depo/what-did-you-learn/SKILL.md`, `README.md`, `agents/openai.yaml`, `references/module-resolution.md`, `scripts/learning_contract.py` | Thin discovery entry plus exact source/installed resource resolution and read-only compatibility checks. |
| TASK-005 | `SKILLS-depo/memory/SKILL.md`, `README.md`, `references/automatic-capture.md` | One shared manual/explicit-save/automatic route, direct module review, memory-only fallback and existing guarded publication. |
| TASK-006 | `SKILLS-depo/memory/references/task-integration.md`, `SKILLS-depo/what-did-you-learn/references/improvement-and-reuse.md`, learning `SKILL.md` | Current ownership, frozen inputs, receipt linkage, concrete improvement disposition, scoped adoption and relevant later reuse. |
| TASK-016 focus | `SKILLS-depo/what-did-you-learn/tests/test_contract.py`, `SKILLS-depo/memory/tests/test_learning_integration.py` | 11 compatibility/no-write tests, 10 learning-body/helper integration tests and one optional-companion discovery regression. |

The read-only resolver API is `resolve(project_root, skill_dir=None)`. Default
resolution uses only the selected root's installed packages; explicit source
resolution uses only its matching source packages. The module manifest hash is
`239f18c84ad93101ae1e67185f70d0ecabe7a0ef65e6156eb5ab0d9d1539af8d`.

The finalized JSON-ready result has `read_only`, `layout`, `module`, expanded
resource/missing/incompatible lists, `memory`, `governance`, `errors` and
`capabilities`. The source [resolver receipt](learning-resolver-result.json)
reports manual review and shared automatic checkpoint interface support as
true with no errors. Publication authority and optional backend readiness both
remain `not_assessed`. Configuration is deliberately not validated by this
static resolver; the initializer performs that separate check with the trusted
memory interface. Resource support is established without importing or executing
the inspected memory package. The supported 1.0.0 minimum covers all 28 memory
package resources and five memory contracts, and every declared Python runtime
file is syntax-checked. A weakened manifest cannot hide absent required files.

## Initial verification evidence

The original complete-run commands, counts and exit codes are preserved in
[learning-final-checks.json](learning-final-checks.json); exact stdout/stderr is
in [learning-final-checks.log](learning-final-checks.log). Each suite ran with
`PYTHONDONTWRITEBYTECODE=1` and the root `.venv/bin/python`:

| Unittest discovery source / pattern | Tests | Result |
| --- | ---: | --- |
| `SKILLS-depo/what-did-you-learn/tests`, `test_*.py` | 11 | Passed |
| `SKILLS-depo/memory/tests`, `test_learning_integration.py` | 10 | Passed |
| `SKILLS-depo/memory/tests`, `test_automatic_capture.py` | 5 | Passed |
| `SKILLS-depo/memory/tests`, `test_publication.py` | 10 | Passed |
| `SKILLS-depo/memory/tests`, `test_recovery.py` | 5 | Passed |
| `SKILLS-depo/memory/tests`, `test_task_integration.py` | 6 | Passed |

Module JSON, all required resources, affected relative Markdown links, Python
syntax and the new skill's bounded metadata/UI fields passed standard-library
checks. `GIT_OPTIONAL_LOCKS=0 git diff --check -- SKILLS-depo/memory LEARNING-depo
SKILLS-depo/what-did-you-learn` returned exit 0. The source package comparison
recomputed hashes for all 35 original memory files outside the four authorized
document changes and found them unchanged. Memory helper scripts, schema,
existing trigger values and persistence APIs were not changed by this worker.

The skill-creator quick validator was attempted with the root interpreter. It
could not import `yaml`; no dependency was installed. The parent accepted the
standard-library metadata/syntax/link checks as sufficient for this bounded
package. The earlier phase checks remain in `learning-task005-checks.json/.log`
and `learning-task006-checks.json/.log`.

## Coverage and observed limitation

The new and retained tests exercise the helper/resource portions of WDYL-01
through WDYL-10, WDYL-13, WDYL-15 through WDYL-17 and WDYL-19: no-write reads and
stdout draft proposals; actual lesson-body publication, receipt, exact/lexical
read and idempotent retry; off with a separately authorized explicit save;
unsupported claims, fields and triggers; discussion evidence; observed failure
receipt; child denial; sensitive/instruction-bearing sources; supersession and
actual partial recovery. The out-of-scope improvement remains body/proposal
content with no target-file creation. Existing six Task-integration tests cover
helper-level packet and owner gates separately from native orchestration.

The first new integration run had two failed assertions because a rejected
attempted publication initializes the existing maintenance lock before evidence
validation. The observed output and correction rationale are preserved in
[learning-initial-test-failures.log](learning-initial-test-failures.log).
Read-only review now uses the existing `validate_publication_evidence` check and
compares every fixture file's bytes and modification time. A separate attempted
write test requires exactly the observed new
`.sys4ai/memory/maintenance/memory.lock`, no note or pending transaction, and
unchanged original record/index/Task/configuration/artifact bytes and times.
The interrupted supersession test separately observes one committed successor
and one pending predecessor, then recovers the exact operation without a Task
write or duplicate active lesson. No production helper was altered to satisfy
the initially incorrect snapshot assumption.

Highest verification reached: relevant broader suites passed, plus actual
source resolver execution and real on-disk helper transactions in disposable
fixtures. Selecting material events, deciding no lesson exists, interpreting an
uncertain cause, and honoring settled meaning remain agent judgments; fixture
inputs are not proof that a native agent made those judgments. Synthetic fixture
grants are not native publication receipts. The actual failing subprocess in
the failure test supplies only its observed exit-code evidence.

Native manual/manager behavior, initialized-project use, selected adoption,
Template/current-root adoption and comparable later improvement remain with the
parent's declared scenarios. No runtime hooks, backend installation, semantic
readiness, external publication, Git commit or long-term benefit is claimed.
This worker made no direct root/Template adoption writes and published no live
learned notes. The bounded implementation/testing stopping condition is reached;
there are no unresolved source defects known within this assignment.

## Optional-companion discovery correction

The parent reproduced an import regression when only memory and MEMORY-depo
were installed: `test_learning_integration.py` unconditionally imported the
optional `learning_contract` module. The original reproduction remains at
[memory-only-test-discovery-before.log](memory-only-test-discovery-before.log).

The correction changes only
`SKILLS-depo/memory/tests/test_learning_integration.py`. It skips the ten paired
integration cases only when both exact learning skill and module roots are
truly absent. `lexists` preserves detection of broken links; a partial package
with no resolver produces an explicit exact-path import diagnostic. When both
packages exist, class setup checks their static compatibility and shared entry
through the unchanged resolver. Partial/incompatible capability is never counted
as a skipped or successful paired integration.

One additional regression exercises memory-only discovery and partial, linked
and incompatible companion states in subprocesses. It runs only the paired
test class inside its nested fixture, so it does not recursively execute its
own discovery test. All original ten integration cases still execute when the
companion is present.

Observed correction results are in
[learning-companion-discovery-checks.json](learning-companion-discovery-checks.json)
and [learning-companion-discovery-checks.log](learning-companion-discovery-checks.log):

| Observed layout or condition | Result |
| --- | --- |
| Current paired source | 11 tests passed, zero skipped, exit 0. |
| Isolated memory-only installed package | One discovery regression passed and ten paired cases were explicitly skipped, exit 0; all installed fixture bytes and mtimes remained unchanged. |
| Module-only or skill-only partial package | Explicit partial-companion diagnostic, exit 1 as expected, no skips. |
| Broken module link | Explicit partial-companion diagnostic, exit 1 as expected, no skips. |
| Isolated complete paired installation | 11 tests passed, zero skipped, exit 0; all installed fixture bytes and mtimes remained unchanged. |
| Incompatible declared module version | Explicit incompatible-companion diagnostic, exit 1 as expected, no skips. |

The corrected test file SHA256 is
`54752c1e99d7bd54bd5a9b9a79bc6acdf7103779388df458e6b58192c7b003dc`.
The source manifest now records that digest. Every other one of its 16 source
artifact hashes was rechecked and remains unchanged, including the initializer's
pinned resolver. SOUL and both assigned role-file digests still match the input
receipts above. No memory runtime, schema, resolver, installed live package or
canonical project state was changed during this correction. The earlier five
unchanged suite results remain 37 passed; the current corrected integration
suite adds 11 passed in paired source use. These are helper/fixture observations,
not proof of native learning behavior. The bounded correction stopping condition
is satisfied.
