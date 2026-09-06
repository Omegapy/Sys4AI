# Memory package location and sharing guidance

## Intent and requirements

Source: the user's request in this conversation to remove ambiguity about
Memory Service when creating personal projects through the template or root
initializer, and when sharing those projects through GitHub.

| Requirement | Acceptance evidence |
| --- | --- |
| LOC-01 | Human and agent entry points name `sys4ai-memory-service`, its public repository, the installed package location and project-private memory storage. |
| LOC-02 | Both manual template copies and generated projects distinguish a locally installed wheel from a package downloaded from GitHub. |
| LOC-03 | Clone guidance requires a real pinned dependency, installation with pip or uv pip, local initialization and verified retrieval; a repository link or requirements file alone is not success. |
| LOC-04 | GitHub repository/releases and optional GitHub Pages documentation have distinct roles; no unverified artifact, tag or Pages URL is presented as available. |

## Bounded implementation plan

1. Update the root README and AGENTS memory entry points.
2. Update the template README, AGENTS and copied INIT_MEMORY guide.
3. Update only SKILL.md and the generated README asset in the reusable
   `SKILLS-depo/init-new-project` package and its active `.agents/skills` copy.
   These two inspected files matched before the change; preserve other assets.
4. Render direct and nested project output through the existing helper, run
   relevant existing initializer checks, validate both skill packages, inspect
   links and review the final diff.

This is documentation and agent-guidance work. Runtime code, package
installation, memory configuration/state, template initialization, existing
consumer adoption, Task/TRD ledgers, Git configuration and publication are
outside this change. Do not add a requirements entry for an unavailable release.

## Current distribution evidence

The read-only GitHub check in this turn reports
`Omegapy/Sys4AI-Memory-Service` as public and empty. Its address is a verified
project location; it is not yet an installable source revision or release.
The existing initializer selects a local immutable wheel under the producer's
`dist/consumer` directory. This guidance change does not implement the pending
portable clone installer or publish the package.

## Verification

| Requirement | Observed result |
| --- | --- |
| LOC-01 | Root and template README/AGENTS plus the generated README name the package, public repository and separate software/data locations. The copied INIT_MEMORY guide identifies the Python import, command and configuration. |
| LOC-02 | The template guide and source/active initializer instructions describe the existing local wheel route. Rendering through `source_snapshot` retained those instructions for both direct and nested project destinations. |
| LOC-03 | Human and agent guidance requires a real pinned dependency, installation, initialization, synchronization and retrieval checks. It explicitly reports the still-missing portable dependency and clone setup rather than claiming implementation. |
| LOC-04 | The guide distinguishes repository/releases from optional Pages documentation, links official pip/GitHub documentation and invents no tag, artifact or Pages address. The public repository was checked and remains empty. |

- Reusable initializer suite: 16 passed; one opt-in installed end-to-end case
  skipped. No dependency installation was performed.
- Template contract suite: 7 passed, including guide links, manual command
  compatibility, starter boundaries and absence of template memory/Git state.
- Source and active skills: both passed `quick_validate.py`; all package files
  match. The two changed files were adopted exactly; version is now `1.0.2`.
- Direct and nested `source_snapshot` renders: README, AGENTS and INIT_MEMORY
  preserve the public repository address and data location; local references
  resolve against generated assets, existing depot assets or prepared memory
  resources. No live project was created.
- Final diff and `git diff --check`: passed. Nine documentation/skill files
  changed, plus this record. Protected registry, runtime source, configuration,
  control records, Task/TRD state, SOUL and ROLE files have no tracked diff.

Highest verification reached: targeted tests passed and generated documentation
was directly inspected. GitHub package installation, a real clean-clone setup,
semantic activation and package/Pages publication were not exercised. The
remaining sharing implementation is a published installable package plus a
portable dependency and supported clone setup procedure.
