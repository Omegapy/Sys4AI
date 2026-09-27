# Project Knowledge Explorer

> Generated from canonical ontology. Edit the owning canonical record, then run build-wiki explicitly.

[Wiki index](INDEX.md)

Stable ID: `urn:sys4ai:ontology:project:sys4ai-depot:capability-project-knowledge-explorer`

Kind: instance. Lifecycle: **approved**. Fact classification: asserted.
Module: project (project-local). Source freshness: current.

A read-only loopback browser exposes Overview, Terms, Processes, and Map for one selected project root. It reads canonical knowledge and permitted sources without authoring or execution authority. Its reading session has no automatic time limit: Close reading session revokes it, and service stop or package replacement invalidates it.

Canonical edit location: [ONTOLOGY/modules/project/project.jsonld#/@graph/90](<../../ONTOLOGY/modules/project/project.jsonld>) `/@graph/90`

## Aliases

- Knowledge Explorer
- read-only ontology browser

## Scope and distinctions

Closing a browser tab alone does not revoke the server session. Bootstrap links and pagination cursors retain bounded lifetimes. Core reads use Python 3.12 and packaged assets without activating optional profiles. Initializer governance-starter-v13 installs static capability without starting a service; the neutral Template does not inherit depot identity, and existing projects need scoped adoption. Recorded capability does not certify complete release verification.

## Relationships

- [Installed ontology skill](installed-ontology-42d57dd9a77d.md) → [provides capability](providesCapability-09a9a79bbe94.md) → [Project Knowledge Explorer](capability-project-knowledge-explorer-9dbae96fcfc8.md) (asserted; approved)

## Sources

- [.agents/skills/ontology/SKILL.md](<../../.agents/skills/ontology/SKILL.md>) `section:Ontology` SHA256 `6b8c22d082031a46c7cf702f6e40f4ea33537c8dad2e3bd08cfd91614676f4a7` (current)
- [SPECS.md](<../../SPECS.md>) `section:Project Knowledge Explorer and initialization v13` SHA256 `20aba9628de8d556d394715aa01d2bc01ed3ddeea5c5bcab4624430dca34d6c4` (current)

## Backlinks

- [Ontology visual workbench](capability-ontology-workbench-ebfeeb597640.md)
- [Ontology skill provides Project Knowledge Explorer](ontology-provides-explorer-3feae4cf2ea6.md)
