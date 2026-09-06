# Sys4AI projects

This directory contains independently owned Sys4AI project working trees.
Known registered projects appear in the parent workspace inventory; a folder's
presence does not register it. Each project owns its files and can own its own
Git repository, history, remote, commits and pushes.

The parent Sys4AI repository tracks this directory guide but does not track
child-project files as ordinary blobs. A child can be recorded by the parent as
a Git submodule after its own repository and remote have been created and
verified.

Registration does not update a child from the reusable root collections. Any
future adoption or refresh of a reusable asset is an exact project-local change
with its own review and tests.

Use the root [init-new-project skill](../.agents/skills/init-new-project/SKILL.md)
for one authorized creation. It uses the registered
[template](./Sys4AI-Template-Project/README.md), six reviewed depot skill packages
and baseline soul, and the immutable Memory Service package. For a clean manual
copy, follow [INIT_MEMORY.md](./Sys4AI-Template-Project/INIT_MEMORY.md) and the
shared `prepare-existing` route. Both routes give the real project isolated
memory and factual inventory without configuring Git.

The template and Memory Service are intended standalone projects, but currently
lack their own Git markers. Do not treat the parent Git repository as their
history. Git setup and publication stay separate from project initialization.
Root memory excludes this entire container, including unregistered projects.
