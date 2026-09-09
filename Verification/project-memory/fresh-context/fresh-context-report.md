# Fresh-context project-memory verification

The bounded recall workflow succeeded. Health, default search, explicit lexical search and canonical record read all exited 0 with empty stderr. Both searches returned the same active canonical finding and README source. The default search actually reported `hybrid`; explicit lexical search reported `lexical`. This is runtime evidence for the inspected root and command sequence, not a project-wide release acceptance.

The before/after bounded snapshot equality is **True** across 287 filesystem entries, with 0 changed entries. Snapshots compare SHA256 content digests, sizes, nanosecond modification timestamps, entry kinds, permissions and symlink targets. They include 216 regular files totaling 74,222,118 bytes at baseline. Full snapshots and exact command stdout/stderr are in [fresh-context-evidence.json](./fresh-context-evidence.json). Only Python bytecode files (`.pyc`, `.pyo`) are ignored; directory entries, including any bytecode directories, are included.

## Identity and authority

- Actual native name: `/root/memory_fresh_recall`, directly returned by `collaboration.list_agents` with that exact path filter and state `running`.
- Function and role: ordinary bounded read-only verifier, `project-sub-agent`; no Task manager, canonical writer, role-index or publication authority.
- The Director's assignment states the directly observed matching `gpt-6-astra` / `max` settings. The child did not change or request settings. The child-side native listing exposes name and status, not model or effort, so the Director's launch receipt remains the evidence for settings equality.
- No parent conversation history was supplied. The answer was discovered through the installed memory CLI. No sibling candidates, other native agents' artifacts, or surrounding release reports were opened to obtain it. The search returned a README excerpt containing a release-report link; that link was not opened.
- The only Verification inputs opened were the canonical record's cited original observation and its referenced original inspection log.

## Governing inputs

| Current file | SHA256 |
| --- | --- |
| `SOUL.md` | `3aa4841fa9f2dc177beabaebd341368d797d224cce3bb18b3fd494f34fa473b2` |
| `AGENTS.md` | `94bf3b72e87a6e2d1a19145977b7d4e879648ab65f9796bf6eb73dfa34135bfa` |
| `ROLE.md` | `b86d3b0bf110816820ed78838f215b7d770dc2ba3073d6fc854dc56507d89e2f` |
| `Roles/project-sub-agent/AGENTS.md` | `7d064ae5d5954af65fc1a83b2ce1c69562d5c31f085e70ac92c3ad0bf2e7eec2` |
| `Roles/project-sub-agent/ROLE.md` | `4c3ac5415030ab770d9af7b73fc773da43d07b041889c77a8755974284c874e2` |
| `.agents/skills/memory/SKILL.md` | `73922a60d6704acd8e87e31294c824d608d7ea80f5b9221e603905603b273bff` |
| `memory.yaml` | `4c855e261c2b80b64f0c026ac21c00eb249ef1e1942b95ec75f0fae86567632e` |

Required root SOUL, AGENTS, ROLE and SPECS, both assigned role files, memory skill and required communication skill were read before the bounded CLI sequence. Initial CLI top-level `--help` and required instruction/configuration reads were preparation before the baseline; the preservation claim covers the subsequent logged inspection sequence.

## Commands and observed outputs

Every command below used this exact prefix:

```text
/Volumes/P-SSD/AngryOwl/Sys4AI/.venv/bin/python -B /Volumes/P-SSD/AngryOwl/Sys4AI/.agents/skills/memory/scripts/memory.py --project-root /Volumes/P-SSD/AngryOwl/Sys4AI
```

| Arguments after the prefix | Observed result |
| --- | --- |
| `health` | Exit 0; ready; read_only true; 1 record; backend available true; prebuilt-profile; basic-memory-v0.23.0; 2 documents; limitation runtime_not_started_by_health. |
| `search --help` | Exit 0; documented modes auto, lexical and hybrid. |
| `search "read-only memory inspection modification timestamps"` | Exit 0; status ok; actual mode hybrid; mutated false; no diagnostics or limitations; matching active memory record plus README.md:203. |
| `search "read-only memory inspection modification timestamps" --mode lexical` | Exit 0; status ok; actual mode lexical; mutated false; same two results; no diagnostics or limitations. |
| `read MEMORY/MEM-20260908-6A59F482.md` | Exit 0; active verified_outcome finding; current canonical hash matches search; no diagnostics. |

Both searches discovered `MEM-20260908-6A59F482`, titled "Root lexical lookup preserves inspected state", before it was opened. The default-mode memory score was 1.2198096762769637 and the lexical score was 34; the README scores were 0.6907012541067404 and 19. Scores are mode-specific and are not compared as confidence measures.

## Reopened evidence chain

| File and locator | Current SHA256 | Observation |
| --- | --- | --- |
| `MEMORY/MEM-20260908-6A59F482.md` (canonical CLI read) | `66555b0f61c19d46f292f37226cfc50481dae531a5114d2af08a7830ec963292` | Active finding with source citations, applicability and explicit limitations. |
| `Verification/project-memory/root-lexical-observation.json`, `json:/outcome` | `4f84c91e22d1aeb419553181e31b3d04f608de61f469273a4dd841d322329811` | outcome passed; observed_at 2026-09-08T21:27:05.712306+00:00; details identify 175 checked files, README.md and disabled backend. |
| `Verification/project-memory/root-lexical-inspection.json`, `json:/before`, `json:/after`, `json:/preserved`, `json:/runs` | `b6ab18ddea2d3ebc73dbfe8b22d048036220bc9ebfcaada73e0bbfece8f6723b` | Original command results and 175-entry before/after snapshots. The serialized before and after objects compare exactly, retaining nanosecond timestamp text without JavaScript numeric rounding. recorded preserved is true. |
| `.agents/skills/memory/scripts/memory_search.py`, `section:def search`, current lines 105-151 | `294877068712251bfde91309e2d444eb47b13f1e8c8ca98e3882684dc4ab7f6b` | Current search dispatch resolves auto through configuration, uses the available configured backend, rechecks source hashes and reports actual mode. Both citations to this file match current bytes. |

The original inspection recorded successful `health`, `search project-local --mode lexical`, and `validate`, each with empty stderr. Health reported backend disabled and zero learned records. Search returned `README.md:54`, "Ownership model", SHA256 `8b5a2aa24dda664ab49fc123a71d46c2a07b429a17a9341d8197800c2d23adc1`; the same current README hash was returned by today's searches. Validation returned valid true. The historical scope listed root governance, README/configuration, MEMORY, Tasks, Roles, memory scripts, memory runtime and depot/projects.json.

This proves that the stored note accurately summarizes the retained versioned command evidence for one earlier lexical-only inspection. It does not retroactively extend that observation to hybrid retrieval. Today's independent command sequence supplies the separate observation of working default hybrid retrieval, explicit lexical retrieval and direct canonical recall under the current root configuration.

## Preservation boundary and limits

The current snapshot covers root `SOUL.md`, `AGENTS.md`, `ROLE.md`, `SPECS.md`, `README.md`, `memory.yaml`, the absent `.codex/config.toml`, and all non-bytecode entries under `MEMORY`, `Roles`, `Tasks`, `.agents/skills/memory` and `.sys4ai/memory`. Snapshots were kept only in process memory until after the final inspection. Evidence files were written afterward, only under `Verification/project-memory/fresh-context/`.

- Preservation is measured at the two observation boundaries. It does not establish that no transient write was made and then reversed between snapshots.
- Access timestamps, extended attributes, filesystem state outside the assigned boundary, remote systems and other processes' internal state were not measured.
- Health's profile readiness is a read-only prebuilt-profile observation and explicitly did not start a runtime. No provisioning, package/model installation, reindex, recovery, publication or configuration change was invoked.
- This query pair is a bounded functional check, not a ranking-quality or performance benchmark. Other source formats and arbitrary queries were not exercised.
- Historical `validate` output was inspected; `validate` was not rerun during this bounded assignment because the required current operations were health, the two searches and record read.
- Native Task-manager integration, future-project initialization, other project adoption, Git, remote publication and whole-release acceptance were not exercised.
- No memory command failed. The original source hashes matched their citations. The first long report payload exceeded the interactive terminal line buffer; it was cleared and finalization completed with a short request. The report was then written within the authorized evidence folder after the unchanged final snapshot.

The assigned stopping condition is reached after this command sequence, source reopening, bounded snapshot comparison and report delivery.
