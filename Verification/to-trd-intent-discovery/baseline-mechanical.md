# Baseline mechanical checks

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s SKILLS-depo/to-trd/tests -v` passed all 46 tests in 6.102 seconds before edits. See [test output](baseline-test-output.txt).

AST parsing and `py_compile.compile(..., cfile=<temporary path>, doraise=True)` passed for the baseline helper and test module. Compiled output was confined to a disposable directory. The suite covers schema, lifecycle, completion diagnostics, legacy reads and migration, exact hashes, locks, read-only behavior, no-ops and privacy. These are helper/storage results, not a reproduced conversation failure. No failing baseline transcript or behavioral root cause was established.
