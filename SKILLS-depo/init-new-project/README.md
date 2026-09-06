# init-new-project

This reusable skill creates one project beneath its owning Sys4AI depot's
`Projects/` directory. The [skill contract](SKILL.md) defines the creation and
manual preparation routes. The helper uses only Python's standard library;
consumer configuration and runtime operations come from the exact installed
Memory Service wheel.

The runtime is installed only after the destination has its final path. Virtual
environments are never copied from the template or moved after installation.
Provider and model activation remain explicitly deferred. Git metadata is
observed only when the exact child has its own marker; no Git mutation command
is implemented.

Run the focused suite from this depot root with Python 3.12:

```bash
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 \
  .venv/bin/python -m unittest discover \
  -s SKILLS-depo/init-new-project/tests -v
```

The installed-wheel end-to-end cases are opt-in. Set
`SYS4AI_INITIALIZER_ARTIFACT` to a verified artifact receipt from the registered
Memory Service and rerun the same suite. These cases construct disposable depot
copies beneath `/private/tmp`, install the exact wheel in each fixture project,
exercise creation and manual preparation, and preserve the live registry and
live projects. An optional `SYS4AI_INITIALIZER_EVIDENCE_DIR` points to an existing
test-owned directory under `/private/tmp` for a concise JSON evidence report.

The unit cases cover destination and identity boundaries, clean seed selection,
complete asset adoption, source drift, atomic registry failures, manual-copy
preservation and interrupted-stage recovery. They do not imply successful
dependency installation or functioning memory unless the installed-wheel cases
also ran.

Receipt schema: [assets/initialization-receipt.schema.json](assets/initialization-receipt.schema.json).
The initializer records source and destination digests after adoption; those
digests describe a reviewed copy, not an automatic synchronization relationship.
