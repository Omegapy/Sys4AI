# Memory registry contract

Registry contract version: 1.0

These UTF-8 CSV files are canonical declarations. Use standard CSV parsing with the exact header order shown in each file. A row states intended identity and policy; it does not prove that an adapter, profile, relation, ingestion, or runtime behavior exists.

Rules common to all registries:

- IDs are stable, case-sensitive, and unique within a registry.
- Trim no meaningful field content. Leading/trailing whitespace outside a quoted field is invalid.
- Use `|` for a set inside one field. Set members cannot contain `|`.
- An empty field means not applicable. Use an explicit `pending-*`, `unassigned`, or `not-implemented` value when the state is unknown or unresolved.
- Reject a row with the wrong column count, duplicate ID, unsupported enum, missing required value, or unresolved reference.
- Registry updates use normal reviewed project changes. Runtime discovery cannot edit these files.
- Exclusion rules take precedence over inclusion rules. With `default_include = false`, an unmatched source is excluded.
- Owner identifies the asset owner or namespace. It does not grant reviewer or approval permission.
- Authority and trust never increase because wording, a relation, a summary, or a provider result appears authoritative.

## Source registry

File: `memory_source_registry.csv`

| Column | Meaning |
|---|---|
| `source_id` | Stable registration ID, independent of a file rename when practical. |
| `project_id` | Exact project scope. |
| `path_or_uri` | One exact repository-relative path or external origin URI. Mutually exclusive with `path_pattern`. |
| `path_pattern` | One repository-relative allow/exclude pattern. Mutually exclusive with `path_or_uri`. |
| `source_kind` | `file`, `external`, `path_rule`, `exclusion_rule`, or another versioned adapter kind. |
| `format` | Declared parser format; known optional families include `pdf`, `html`, `docx`, `xlsx`, `pptx`, `image`, `audio`, and `domain`; `any` is valid only for exclusion rules. |
| `canonicality` | `canonical`, `evidential`, `generated`, `episodic`, `scratch`, or `excluded`. |
| `content_role` | Stable role such as governance, decision, configuration, or external evidence. |
| `authority_tier` | `A0` through `A7` under the architecture contract. |
| `trust_class` | One approved trust class from the architecture contract. |
| `sensitivity` | `public`, `internal`, `confidential`, `restricted`, or `secret-prohibited`. |
| `namespace` | Retrieval namespace. Governance and external evidence use separate namespaces. |
| `profile_id` | Exact registered profile that interprets this source. |
| `ingestion_adapter` | Registered adapter ID or `none` for exclusions. |
| `chunking_profile` | Registered deterministic chunking profile or `none`. |
| `schema_ref` | Repository-relative validation schema when the source requires one. |
| `refresh_mode` | Revision strategy such as `git-revision`, scheduled, manual, or static. |
| `retention_policy` | Approved retention-policy ID, `canonical`, or `none`. |
| `owner` | Asset owner/namespace; not an approval grant. |
| `write_policy` | Approved write-policy ID or `deny`. |
| `include_flag` | Lowercase `true` or `false`; false is an exclusion/disabled rule. |
| `notes` | Concise non-secret context. It has no authority beyond the row. |

Repository ingestion provenance adds the observed commit/blob or explicit working-tree state, content hash, adapter/profile versions, timestamp, and sanitized warnings. External-source provenance also adds origin URI, retrieval time, license/retention metadata where available, and content hash.

The base formats use built-in deterministic adapters. Optional and domain
formats require an explicitly supplied adapter whose ID and format match the
registration exactly; merely adding a row never installs or enables a parser.

## Profile registry

File: `memory_profile_registry.csv`

| Column | Meaning |
|---|---|
| `profile_id` | Stable public identifier, including major line, such as `base@1`. |
| `profile_name` | Human-readable name. |
| `profile_version` | Exact semantic version of the profile definition. |
| `lifecycle_status` | Decision state, such as `approved-contract`, active, deprecated, or retired. |
| `implementation_status` | Separate observed state, such as `not-implemented`, partial, or verified. |
| `extends_profile_id` | Parent profile ID; blank for the base profile. Cycles are invalid. |
| `schema_ref` | Repository-relative profile schema. |
| `config_ref` | Repository-relative configuration source. |
| `record_types` | Pipe-delimited types declared by the profile. |
| `relation_types` | Pipe-delimited registered relation names. |
| `source_adapters` | Pipe-delimited implemented adapters; `none-implemented` does not claim support. |
| `write_policy_ref` | Repository-relative or registered policy reference. |
| `migration_ref` | Migration from the prior profile line, if applicable. |
| `api_compatibility` | Public API version constraint. |
| `owner` | Profile asset owner; not reviewer authority. |
| `authority_basis` | Decision/ADR identifiers that authorize the profile contract. |
| `notes` | Concise limitations or context. |

An extension may add types, relations, adapters, query intents, and write rules. It cannot alter a base type or relation meaning. Such a change requires a new major profile and migration.

## Relation registry

File: `memory_relation_registry.csv`

| Column | Meaning |
|---|---|
| `relation_id` | Stable registry-row ID. |
| `relation_name` | Public uppercase relation type. |
| `relation_version` | Exact semantic version of its meaning. |
| `lifecycle_status` | Decision state of the relation contract. |
| `implementation_status` | Separate observed implementation state. |
| `profile_id` | Profile that owns the relation meaning. |
| `source_types` | Pipe-delimited permitted source types or `*` pending narrower profile rules. |
| `target_types` | Pipe-delimited permitted target types or `*` pending narrower profile rules. |
| `directionality` | `directed` or `bidirectional`. |
| `symmetric` | Whether reversing endpoints preserves meaning. |
| `transitive` | Whether transitive inference is permitted. Base rows default false. |
| `inverse_relation` | Registered inverse relation name, when one is defined. |
| `authority_effect` | Must be `none` for the base contract. A relation cannot raise authority. |
| `validation_rule` | Pipe-delimited checks required before activation. |
| `schema_ref` | Repository-relative relation-record schema. |
| `owner` | Relation-definition owner; not approval authority. |
| `authority_basis` | Source requirement or decision. |
| `description` | One-sentence semantic definition. |
| `notes` | Concise limitations or context. |

`symmetric = true` does not authorize the provider to create a second canonical edge. It permits equivalent query traversal. `transitive = false` forbids inferred chains unless a later versioned relation contract explicitly permits them. Every stored edge still carries endpoint IDs, project scope, provenance, status, and validation/confidence information.

## Base registration state

`base@1` and the approved `software-engineering@1` extension are registered and
verified. Base relation rows retain their individual implementation status;
the software profile owns four separately named verified declarations. This
separation prevents a declaration from silently changing a base meaning.
Source rows register canonical permissions and both profile definitions while
continuing to deny derived, model, environment, and key paths.
