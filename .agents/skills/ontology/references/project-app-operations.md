# Project app operations

Open **Launch Project.command** from the selected project in Finder. It starts
or reopens that project's compatible local reader and opens Home after readiness.
A missing prerequisite opens **Project App Setup.html**. No launch installs
packages, starts optional backends, or generates Home prose.

For an explicit terminal launch with the project's Python 3.12:

```sh
.venv/bin/python -I -S -B .agents/skills/ontology/scripts/project_app.py --project-root . --open
```

**Close reading session** revokes the browser's session. Closing a tab alone does
not revoke it. **Stop app** stops the selected project's owned reader and ends
its sessions. A trusted local stop uses the same authenticated ownership check:

```sh
.venv/bin/python -I -S -B .agents/skills/ontology/scripts/project_app.py --project-root . --stop
```

Reopen the launcher for a fresh session. The browser cannot restart a stopped
service. Bootstrap links and private service receipts are credentials: keep them
out of reports, shared links and Git. Copy controls copy logical references or
instructions; they do not run the instructions.

## Project content and available readers

`project-app.json` contains project-owned Home explanations, selected supporting
documents and reviewed source hashes. Its project ID must match `project.json`.
The depot can instead use its exact registry self entry. Neutral Template content
has no project ID and cannot impersonate the depot.

Empty sections remain labeled gaps. An owner drafts and reviews purpose, scope,
audience and Start here against permitted project documents. Record the exact
text digest, source digests and review time using the
[content contract](project-app-contract.md). Changed supporting bytes mark a
review need; revoked or unavailable sources withhold dependent prose. Browsing
never edits it. Keep custom prose out of the shared build and Template.

Work displays canonical Task information and explicit links, while requirements
approval, plan lifecycle, recorded assignments, completion and release evidence
retain separate meanings. Project knowledge reuses the existing Explorer; Lessons
and decisions searches permitted memory. A missing or incompatible owner affects
only its integration. Health reports static capability and recorded notices,
including what has not been checked. It does not run repairs or start a backend.

## Build and delivery

[BUILD.md](../explorer/BUILD.md) owns the pinned toolchain, source inventory and
explicit build/publisher. Use the existing lock; any missing prerequisite requires
its separately selected restoration. Launch never builds. After authorized
source changes, run the documented strict build and runtime publisher, retain
the exact `.explorer-build.json` receipt, and distribute the complete reviewed
package through the Template updater. Do not mix chunks from different builds.

New and first-prepared projects receive static app capability through initializer
`governance-starter-v14`. For one selected earlier completed setup, run the depot's
installed initializer with that project's existing identity:

```sh
.venv/bin/python .agents/skills/init-new-project/scripts/init_new_project.py prepare-existing \
  --destination /absolute/depot/Projects/SelectedProject \
  --project-id selected-project --project-name 'Selected Project' \
  --purpose 'The existing recorded project purpose' --adopt-module project-app
```

Replace the example with the actual selected path and recorded identity. The
existing beneath-Projects destination limit remains enforced. The depot root
uses separate exact manifest adoption, never this child-project route.

The setup receipt retains its original edition and app module source, target,
configuration and executable-mode provenance. Existing Home text and launcher
files are preserved. A complete unchanged receipt-owned shared reader package
can be updated as one unit; customized or incomplete packages require a separate
reviewed adoption. An ordinary completed rerun does not refresh new source bytes.

## Recovery

For interrupted setup, preserve working files, resolve the stated conflict and
repeat the exact module request with its frozen Template inputs. Do not reset
receipts or overwrite newer project edits. For package changes, stop the owned
reader before relaunching. If the current package is incomplete, restore the
exact reviewed package through its owner; do not repair it during browsing.

Before an explicit package rollback, retain current preimages and stop the owned
service. Restore only the reviewed operation-owned package/configuration bytes
and modes when they still match the recorded postimages. An enabled guard needs
its public exact repair route and coherent adapter/bootstrap/config bindings.
Never restore old Task, ontology, memory, setup history or publication records
as a package rollback. Conflicting current files require review.

Standalone Knowledge Explorer remains available:

```sh
.venv/bin/python -B .agents/skills/ontology/scripts/ontology.py --project-root . explore --open
```

Current delivery checks and actual limitations are recorded separately in
`Verification/shared-project-app/RELEASE.md` at the depot. Static capability,
fixture evidence and an observed browser session are different evidence levels;
none implies Git publication, deployment or adoption into another real project.
