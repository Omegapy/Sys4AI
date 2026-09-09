# Learning skill package

Version 1.0.0 is a thin entry to the substantive `LEARNING-depo` module and
the existing memory completion procedure. Start with [SKILL.md](SKILL.md).
The module owns policy and the eight-step review; this package owns discovery,
[resolution](references/module-resolution.md) and
[improvement/reuse routing](references/improvement-and-reuse.md).

The standard-library `scripts/learning_contract.py` performs read-only static
resource/interface checks. It neither evaluates lessons nor publishes records.
Its tests exercise source and installed layouts, incomplete or unsafe packages,
legacy completion compatibility and no-write results. Memory integration tests
exercise the actual existing persistence helpers in isolated fixtures. Neither
test category proves native agent judgment or background event detection.

From the owning depot run:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s SKILLS-depo/what-did-you-learn/tests -v
```

Publish reusable changes through the Template updater. Adoption of active or
existing projects is separately scoped; copying this package grants no memory
publication or project-change authority and copies no learned history.
