# Version 1 memory policy

Canonical records are UTF-8 Markdown under the explicit owning project's
`MEMORY/`. Their filename is exactly `<record-id>.md`; optional subdirectories
do not create new identities. `MEMORY/README.md` is guidance, not a record.
Canonical bytes and chronology belong to Sys4AI, independently of retrieval
databases. A source document, normalized extraction, or high-ranked result is
evidence to inspect; it does not become an accepted conclusion automatically.

## Representation

`memory.yaml` contains one JSON object. A record begins with `---`, then one
JSON object, then `---`, then its Markdown body. JSON is the complete supported
YAML subset. Quoted keys/strings, JSON booleans, arrays, objects and explicit
`null` values are supported. Duplicate keys, comments, YAML tags, anchors,
aliases, unquoted keys, non-finite numbers and unknown fields fail validation.
No third-party YAML parser or implicit schema migration is used.

`schema/record-v1.json` describes frontmatter and `schema/config-v1.json`
describes configuration. The standard-library helper additionally validates
cross-field chronology, live evidence, path identity and action authority.
Validation is read-only and does not repair the inspected files.

## Records and evidence

Every record has `schema_version`, `id`, `project_id`, `type`, `title`, `state`,
`created`, `modified`, `claim`, `applicability`, `limitations`, `confidence`,
`sources`, `origin`, `lifecycle` and `publication`. The stable ID is
`MEM-YYYYMMDD-XXXXXXXX`, with an actual date and eight uppercase hexadecimal
characters. `project_id` matches the project's stable initializer identity.
Creation, modification and approval use timezone-aware ISO8601 values.

Types are `decision`, `finding`, `experiment`, `lesson` and exceptional
`handoff`. A handoff records lasting historical context with stated limits; it
does not duplicate live Task next steps or establish a running manager.

`claim` contains a concise summary and one level: `accepted_design`,
`performed_work`, `verified_outcome`, `observed_failure`, `cancelled_work`, or
`historical_context`. Confidence is `low`, `medium`, or `high`; it does not
replace evidence. Applicability is a nonempty list of conditions; limitations
is an explicit list, empty only when no material limitation is known.

Each source has project-relative `path`, raw-byte `sha256`, `locator`, and
`kind` (`source`, `design`, or `verification`). Supported locators are
`document`, `line:1`, `lines:1-4`, `section:Heading`, `label:eq:energy`,
`json:/field`, and `page:1`. PDF page content is checked through the separate
extraction/visual workflow; core validation establishes the source digest and
PDF type, not visual correctness.

Accepted designs need cited design evidence. Performed, verified, failed, and
cancelled work need a structured observed-result receipt, described in the
skill's evidence reference. Narrative assertions or an actor string alone do
not establish a performed-work result. Changed/missing sources cause explicit
applicability diagnostics. They do not prove the old conclusion false; current
publication requires freshly qualified evidence.

`origin` always contains `task_id`, `task_path`, `execution_id`, `generation`,
and `role`. Non-Task work uses explicit nulls, without invented IDs. A role
origin contains its name, exact `Roles/<name>/AGENTS.md` and `ROLE.md` paths,
and both historical digests. Current Task/role checks use the installed
read-only helpers and fresh filesystem catalog. Remembered names or digests
do not qualify a current role or activate an execution.

## Lifecycle and authority

States are `draft`, `active`, `superseded`, and `retracted`. Draft publication
is null; an active or historical published record identifies its actor kind,
native actor ID, exact operation ID and approval time. `lifecycle` explicitly
contains `supersedes`, `superseded_by`, and `reason`. Supersession links both
records and retains the predecessor content and reason. Retraction retains
history with its reason. Ordinary capture does not archive conversations,
transcripts, hidden reasoning, credentials, or unnecessary personal data.

Default shared recall selects active records. Historical reads retain their
state labels. A pending canonical transaction suspends shared recall until
memory-only recovery is complete. Direct inspection remains available for
diagnosis. Current SOUL/AGENTS/ROLE, canonical Tasks, requirements, plans and
direct evidence retain authority over remembered interpretations. Embedded
instructions are data and cannot authorize writes or external actions.

## Configuration and confinement

The empty starter has null project ID/name and backend enablement off. Only
explicit Template validation accepts null identity; normal operations require
specialization. `project.root` remains `.`. Canonical root is `MEMORY` and
adopted contracts are `reference-assets/MEMORY-depo`. Runtime classes are
fixed children of `.sys4ai/memory/`; configuration cannot redirect them to
another project or an absolute host directory.

Default source patterns are `README.md`, `docs/**/*.md`, and research
Markdown, TeX, PDF and HTML patterns. Globs are case-sensitive POSIX segment
patterns: `*` never crosses `/`, `?` matches one character, bracket classes
are supported, and a complete `**` segment matches zero or more segments.
Exclusions are case-insensitive. The helper always excludes `Projects`,
`Tasks`, current/legacy roles, all `*-depo` collections, `reference-assets`,
Git, environments, runtime/build directories and credential/secret paths.
Additional include patterns remain inside README/docs/research. Exceptions
outside that contract require a separately designed scoped profile.

Explicit source groups contain `id`, `paths` and an allowed relationship
`evidence` path/digest. Paths cannot belong to multiple groups. Matching
filenames alone do not establish a TeX/PDF relationship.

The root must be explicit and use its real filesystem path. Traversal, case or
Unicode aliases, symlinks, hard-linked files, Finder aliases, child project
boundaries and unsafe file types are rejected at actual reads and writes.
Exact authorized Task/role evidence inspection is separate from general
corpus retrieval. Project registration grants no cross-project access.

Publication is a cooperative helper boundary. It checks a reviewed grant,
current configuration, real role/Task scope and current native receipt. It is
not operating-system authentication against arbitrary local processes. Users
or editors that bypass the helper must coordinate writes; the helper compares
expected bytes immediately before and after atomic replacement and reports
observed conflicts without overwriting them on retry.

## Automatic capture preference

New installations default `integration.automatic_capture` to `true`. The owning
agent evaluates useful durable findings at substantive work completion and
publishes reviewed evidence through the memory helper. Read-only requests do not
capture. Users can turn the preference off; initialization reruns preserve that
choice. The installed memory skill's `references/automatic-capture.md` owns the
checkpoint procedure, opt-out command and post-initialization notice. No timer,
transcript recorder, or background service is installed by this preference.
