# Dependency workflow

Read the current dependency contract in `reference-assets/CURATION-depo/dependencies.md`.
`curator_dependencies.inventory` validates exact typed declarations.
`pypi_version_response` parses a bounded selected official version response;
`assess` distinguishes not-due, pending evidence, competing updater, security,
upgrade candidate, retained compatible pin and current pin. No function performs
network I/O or installation. Record exact primary evidence and its limitations.

`candidate` requires separate declaration/source/install/service permissions and
an unchanged candidate environment. Major/backend/schema/storage transitions
require protected review. Route accepted source edits through reviewed
integration and runtime effects through the selected existing runtime owner.
