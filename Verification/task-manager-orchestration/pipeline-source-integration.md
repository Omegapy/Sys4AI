# Live source/depot pipeline integration

The exact reviewed 15-file component was applied to sources and depot tooling;
all component before/after hashes were checked. Root skills and the Template
were not included in that publication. The updater and watcher source suites
pass 38 and 11 tests respectively.

The first plain initializer test run found a test-setup dependency on the new
live Template role directory before that Template was authorized for publication.
All 36 errors occurred at fixture construction. Running the unchanged actual
source tests against the checked disposable Template passed 36 tests. Root then
removed the circular fixture dependency: the disposable test Template is composed
from the current explicit source mappings and source packages, preserving existing
unmapped historical starters. The production helper still reads only the fixture's
registered Template. No validation assertion or behavior gate was removed.

The normal direct source command now passes all 36 tests without an environment
overlay or fixture monkeypatch. See [the final receipt](pipeline-checks/initializer-source-final.json)
and retained earlier logs. The source test fixture is the sole root follow-up
change to the component snapshot; final publication/adoption manifests include
its current hash. This also keeps source development testable before live adoption.

Current tests cover generated-index ownership and exact recovery, custom-role
conflicts, retained legacy pair retirement, old receipt recovery, full package
preservation, actual transition followed by preparation/rerun, and rejected
partial/corrupt transition evidence with unchanged bytes. Earlier independent
component receipts remain in [pipeline/](pipeline/).

The exact live Template delta has eight additions, thirty updates and two
legacy role retirements. It contains no To-TRD, Task history, TRD, historical plan
or other-project update. The retired pair's original bytes are retained by the
updater before deletion. The reviewed [manifest](template-adoption-manifest.json)
and [preview](template-preview.json) bind every destination and source digest.
This source gate does not claim Template or active-root publication.
