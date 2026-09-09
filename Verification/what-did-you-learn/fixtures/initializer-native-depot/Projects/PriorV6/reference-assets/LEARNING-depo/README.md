# What Did You Learn module

Version 1.0.0 connects discussion and work evidence to useful lessons,
improvement decisions and later comparable use. This collection owns the
substantive [policy](policy.md), [eight-step review](review-contract.md),
[compatibility manifest](contract.json) and [lesson body](assets/lesson-body-template.md).
It contains reusable capability, never learned records or project runtime state.

The thin `what-did-you-learn` skill resolves these assets and the owning
project's memory package. The existing memory skill owns retrieval,
publication, lifecycle and recovery. Its `references/automatic-capture.md`
is the single completion entry for both skills. A manual review is available
without save authority; a useful review can end with nothing to save.

Author this module in `LEARNING-depo/` and the skill in
`SKILLS-depo/what-did-you-learn/`. The Template updater maps the module to
`reference-assets/LEARNING-depo/` and the skill to
`.agents/skills/what-did-you-learn/`. Initialization uses those Template assets.
Active root or existing product adoption requires an exact selected destination
and preservation boundary. Keep each project's accepted lessons in its own
`MEMORY/` through its installed memory helper.

`contract.json` declares versioned resource and interface requirements. It has
no project identity, grant, capture preference, record inventory or installation
status. The learning skill's read-only `scripts/learning_contract.py` checks
source and installed layouts. Its static results do not establish current
publication authority, a running backend, successful agent judgment or actual
checkpoint execution. No runtime hook, scheduler, service or package install
is part of this module.

Observed post-adoption project-owned addition.
