# Consumer preparation

Use the installed runtime package to prepare project-owned canonical memory
files. The caller must already have authority to write this exact project.
The project directory must exist, have an absolute path without symlinks, and
have a distinct lowercase project ID.

```python
from pathlib import Path
from sys4ai_memory.bootstrap import prepare_project_memory

result = prepare_project_memory(
    Path("/absolute/project"),
    project_id="example-project",
    project_name="Example Project",
    principal_id="project-owner",
)
```

The equivalent installed-package command is:

```bash
python -m sys4ai_memory.bootstrap prepare \
  --project-root /absolute/project \
  --project-id example-project \
  --project-name 'Example Project' \
  --principal-id project-owner
```

The result reports dataset `example-project-memory`, configuration
`config/memory.toml`, resource version, written files, and deferred semantic
activation. Configuration, registries, profiles, policy references, schemas
and permissions are specialized from `importlib.resources`. Neither route
reads an editable sibling checkout or copies runtime source into the consumer.

Preparation validates the complete proposed file set in a disposable directory
before publishing it. Equivalent canonical files retain their exact bytes and
modification times. Conflicting files, identity changes, unsafe paths and
permission changes fail without replacing project files. Existing ignore rules
are preserved, and a final exclusion block protects generated memory and local
credentials. A retry completes any missing files after an interrupted write.
Concurrent external edits are detected at the publication check; exclusive
file creation refuses to replace a file that appears later.

The initial source registry names only project-local `AGENTS.md`, `SOUL.md`,
`ROLE.md` and `README.md`. Other folders remain excluded until reviewed source
registration admits them. Pass `allow_source_registration=True`, or the CLI
flag `--allow-source-registration`, only when the named owner is explicitly
authorized for that existing administrative operation. This option grants no
other administrative action and does not register any additional source.

Preparation leaves `.sys4ai/memory/` uninitialized. Use the existing shared
`init-memory` CLI or `MemoryClient.initialize` API next. The canonical and manual
project-creation routes use that direct initializer with no preview or digest.
The depot's separately reviewed adoption may use the existing preview/apply
entry point against the same prepared configuration and storage implementation.

The default `base@1` configuration enables exact and lexical retrieval only.
The optional software-engineering profile includes its complete references but
requires explicit semantic-model choices and trusted profile-source authority
before activation. Preparation never imports native provider code, opens a
listener, loads a model, or downloads model weights. Successful initialization
receipts are emitted by the shared initializer after storage creation; prepared
canonical files never contain a fabricated success receipt.

The `consumer_v1` bundle has version `1.0.0`. Its shipped JSON Schemas are
snapshots of the runtime's public contracts, profile definition, configuration,
and canonical permission document. The packaging tests check these snapshots
against the installed runtime models and validate every generated reference.
