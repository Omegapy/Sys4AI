---
name: curate
description: Inspect an explicitly selected project Curator policy and report missing capability, authority or runtime proof without activating work.
---

# Curator foundation

Use this skill when the user explicitly requests Curator policy inspection.
Read the selected project's SOUL.md and governing instructions first. Installation
and reading CURATOR.md confer no activation or standing authority.

The current command interface is read-only:

```sh
python scripts/curator.py status --policy /absolute/project/curator.yaml
python scripts/curator.py validate --policy /absolute/project/curator.yaml
```

Use the project's selected Python interpreter. Both commands read one bounded
JSON-compatible YAML policy. They create no Task, grant, file, service, network
request or model call. Neutral settings report installed_inactive and the exact
missing selections. A selected configuration still requires current runtime
and confinement evidence before operation admission.

The [foundation interfaces](references/foundation-interfaces.md) describe the
policy boundary. Native release gates are described in the
[native protocol](references/native-protocol-v1.md).
