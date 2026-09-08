# Sys4AI licensing depot implementation

Source: the user's 2026-09-08 request to reuse the three licensing files from
`/Volumes/P-SSD/Omegapy/My-Academics-Portfolio/` in a new `LICENSES-depo`, the
active Sys4AI root, the registered Template, and project initialization.
This is an ordinary implementation record, separate from managed TRDs, Tasks,
and the native goal.

## Requirements and acceptance

| ID | Requirement and source | Observable acceptance |
| --- | --- | --- |
| LIC-001 | Reuse the supplied three-file licensing structure (user request and supplied files). | `LICENSES-depo/LICENSE` routes code to Apache 2.0 and documents to CC BY 4.0; both companion files contain complete official terms and retain the supplied attribution. |
| LIC-002 | Apply the system to the active root (user request). | The root has all three source-identical files and its guidance links to the licensing source. |
| LIC-003 | Apply the system to the registered Template like other depots (user request and update guide). | Explicit mappings publish all three files at the Template root; an updater check reports current with no conflicts. |
| LIC-004 | Include licenses in new and existing project initialization (user request). | Both routes use the Template trio, with source/adoption hashes; existing licensing is preserved as a set and missing companion files are not silently added to a different system. |
| LIC-005 | Preserve project ownership and existing setup history (root AGENTS.md and initializer contract). | Earlier receipt editions still resume or rerun under their original contract; no unrelated product, registry, source-example, Task, TRD, or Git changes occur. |

## Decisions and implementation plan

The supplied license texts contain omission placeholders. Keep their intended
Apache 2.0 / CC BY 4.0 split and replace those excerpts with the complete texts
from the publishers. Make `LICENSE` a concise scope and attribution notice;
legal terms live in the companion files. Retain Alexander Samuel Ricciardi and
the supplied 2025 attribution by default. Distinguish inherited attribution
from project-specific notices. Separately licensed material retains its notices.

1. LIC-001: Add the source trio and a short provenance/adoption guide to
   `LICENSES-depo/`. Compare the companion legal-code bodies with downloaded
   official bytes and record source hashes.
2. LIC-002/003: Add explicit Template overrides, root copies, and concise
   navigation/specification updates. Use the existing updater; keep its normal
   ownership and conflict checks. Preserve unrelated work already in this tree.
3. LIC-004/005: Update the reusable initializer, then adopt only its changed
   files into the root. Introduce `governance-starter-v4` for mandatory licenses,
   retaining v1-v3 source allowlists and recovery semantics. Preserve existing
   license markers and canonical companions with explicit receipt evidence.
4. LIC-001 through LIC-005: Run source initializer and updater tests, root and
   Template checks, and installed-helper CLI create/prepare/rerun workflows in
   disposable depots. Review a current source/root/Template hash manifest and
   requirement coverage before closing the native goal.

Dependencies: existing Python 3.12 standard-library helpers, registered Template,
and the official license texts. No new runtime packages are needed. Temporarily
stop and restore the existing watcher during the coordinated source/policy edit.

Risks: truncated source terms, mixing existing license systems, invalidating old
receipts, and replacing unrelated edits. Controls: complete official bodies,
whole-system preservation, contract-aware validation, and a pre-edit snapshot.
No publication, bulk product adoption, or legal enforceability claim is in scope.

## Verification record

Implemented and verified locally on 2026-09-08. All LIC-001 through LIC-005
acceptance criteria passed. The [verification packet](../Verification/licenses-depot/verification.md)
contains the requirement matrix, exact source/adoption hashes, independent
review result, project test outcomes, seven installed-CLI workflows, and observed
live watcher status. The tests used disposable projects; no ordinary product
was created, relicensed, or published. The supplemental skill-creator validator
was unavailable because PyYAML is not installed; project validators passed.
