# Preservation audit

Every preserved path from canonical plan revision 2 was compared with its pre-edit inventory. All 24 match. Regular-file SHA-256 and symlink inventories were compared; package cache directories and .DS_Store are excluded. [Machine results](preservation-results.json), [initial inventories](baseline.json).

| Preserved path | Type/count | Result |
| --- | --- | --- |
| `TRDs/` | directory, 5 files | Unchanged |
| `Tasks/` | directory, 138 files | Unchanged |
| `AGENTS.md` | file, 1 files | Unchanged |
| `SOUL.md` | file, 1 files | Unchanged |
| `ROLE.md` | file, 1 files | Unchanged |
| `SPECS.md` | file, 1 files | Unchanged |
| `depot/projects.json` | file, 1 files | Unchanged |
| `depot/template-update.json` | file, 1 files | Unchanged |
| `tools/template_update.py` | file, 1 files | Unchanged |
| `tools/template_watch.py` | file, 1 files | Unchanged |
| `.agents/skills/to-trd/` | directory, 14 files | Unchanged |
| `SKILLS-depo/to-trd/scripts/trd.py` | file, 1 files | Unchanged |
| `SKILLS-depo/to-trd/ATTRIBUTION.md` | file, 1 files | Unchanged |
| `SKILLS-depo/to-trd/licenses/wayfinder-MIT.txt` | file, 1 files | Unchanged |
| `SKILLS-depo/agent-task/` | directory, 8 files | Unchanged |
| `SKILLS-depo/task/` | directory, 3 files | Unchanged |
| `SKILLS-depo/to-implementation-plan/` | directory, 14 files | Unchanged |
| `Implementation_Plans/project-specifications-adoption.md` | file, 1 files | Unchanged |
| `Implementation_Plans/subagent_role_system_implementation_plan.md` | file, 1 files | Unchanged |
| `Implementation_Plans/sys4ai_synchronization_removal_implementation_plan.md` | file, 1 files | Unchanged |
| `Implementation_Plans/task_system_implementation_plan.md` | file, 1 files | Unchanged |
| `Implementation_Plans/template_source_pipeline_implementation_plan.md` | file, 1 files | Unchanged |
| `Implementation_Plans/to_implementation_plan_skill_implementation_plan_2026-08-28.md` | file, 1 files | Unchanged |
| `/Users/alex.omegapy/Downloads/Sys4AI_to-trd_Intent_Discovery_Recommendations_2026-09-07.md` | file, 1 files | Unchanged |

The selected canonical plan also retains revision 2 and its initial digest; read-only validation reports current projections. The source TRD remains draft revision 1. Active-root to-trd retains all 14 baseline resource hashes. Source and mapped Template now contain the identical 16-resource candidate. No root or ordinary-product adoption, registry edit, Task mutation, Git mutation, publication, watcher installation or service control was performed.

The baseline-to-candidate source diff changes exactly the 13 files in candidate-manifest.json; helper/provenance hashes are unchanged. The mapped Template received only this package through the existing pipeline. Git differences in the protected helper predate this execution and are retained in the baseline. Source/readback evidence does not claim future project creation or fresh-host behavior.
