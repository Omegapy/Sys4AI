# Communication skill

This repository-local Codex skill sets the default writing and editing voice
for work in The-AEther-Flow_v0. It preserves facts, source support, protected
wording, and the user's requested scope while removing formulaic writing.

## Origin

The communication skill was inspired by the
[Unslop skill](https://github.com/cursor/plugins/tree/main/pstack/skills/unslop).
This project maintains its own communication instructions in `SKILL.md`.

## Project scope

The repository's `.codex/config.toml` disables the personal global Unslop
skill at `/Users/alex.omegapy/.codex/skills/unslop/SKILL.md` only while Codex
works in this trusted project. It does not remove or modify the global skill,
so Unslop remains available in other projects.

Restart Codex after changing project skill configuration if the active skill
list does not refresh automatically.
