# Sys4AI projects

This directory contains independently owned Sys4AI project working trees.
Known registered projects appear in the parent workspace inventory; a folder's
presence does not register it. Each project owns its files and can own its own
Git repository, history, remote, commits and pushes.

The parent [Omegapy/Sys4AI repository](https://github.com/Omegapy/Sys4AI) tracks
this directory guide and the Template as an ordinary directory:

- [Sys4AI Template Project](./Sys4AI-Template-Project/README.md)

All other project working trees remain excluded. Each included project's local
ignore rules still protect credentials, environments, caches and generated
runtime data.

Registration does not update a child from the reusable root collections. Any
future adoption or refresh of a reusable asset is an exact project-local change
with its own review and tests.

Use the root [init-new-project skill](../.agents/skills/init-new-project/SKILL.md)
for authorized creation or preparation of an existing project. It obtains
starter assets only from the registered
[Template](./Sys4AI-Template-Project/README.md), specializes project identity,
preserves customized content, and records factual inventory. The Template
receives automatic updates from reusable source collections; resulting product
copies remain independent.

The Template has no independent Git repository or remote. Environment and
product dependency setup, Git initialization, and publication remain separate
from governance setup.
