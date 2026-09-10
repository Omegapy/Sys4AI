# Template-copy verification

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s Projects/Sys4AI-Template-Project/.agents/skills/to-trd/tests -v`: **46/46 passed**, 6.406 seconds. [Output](template-test-output.txt). This invokes the Template's own test and helper files.

Template AST parsing, compilation into disposable output, JSON example parsing and package/link/metadata checks passed. Source/Template parity is 16/16 final resources, including preserved helper, attribution and license. Active-root remains 14/14 baseline resources at 2.1.0. [Results](static-results.json), [manifest](candidate-manifest.json), [preservation audit](preservation-audit.md).

The bundled external YAML skill validator could not run because PyYAML is absent, as described in [source verification](source-mechanical.md). The Template was checked as a package and mapped filesystem result; no future-project creation, product adoption, or actual-host conversation was exercised. Root TRD validation was read-only and canonical-valid; it did not migrate records or repair the index.
