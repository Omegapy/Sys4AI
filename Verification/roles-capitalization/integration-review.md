# Director integration review

The Director inspected the active-path consumers, role receipt protocol,
initializer edition handling and Template case-rename transaction.

The Task helper now accepts original lowercase pair metadata during structural
history validation but requires the actual `Roles` directory, current catalog
and exact pair paths for a new live assignment. Case aliases of the role root
and index are excluded from worker write scopes. Its source suite passes 92
tests; four discriminating path/control/delivery tests also pass on a real
case-sensitive APFS filesystem.

The role helper uses exclusive OS directory rename primitives through Python's
standard-library ctypes, preserving an independently appearing destination.
It binds a two-hop rename to the exact directory identity and tree inventory.
Original transition receipts remain byte-identical; completed case evidence
maps earlier paths without pretending that historical hashes are current.

One updater finding remains under correction: its initial `exists()` followed
by `os.rename()` can replace an empty directory created at that boundary.
The updater worker is reproducing this case and replacing only those hops
with the same exclusive-rename behavior. Live root/Template adoption waits for
the regression and relevant passing rechecks. Earlier passing test receipts
remain attributable to their original code snapshot.

The initializer uses a new v3 edition for `Roles/`; earlier v1/v2 histories
remain supported without rewriting their source/adoption maps. An explicit
completed case proof is required to resolve a v2 receipt at its current physical
paths. Native role loading and delivered Template/root adoption are still
separate final checks.

The updater collision was reproduced and corrected with exclusive rename; both 59-test updater/watcher runs passed. Live adoption subsequently passed. The first integrated root suite also exposed its old current-adoption assertion: it compared the new initializer to the previous plan's immutable manifest. The test now checks the actual capitalization adoption receipt and still verifies that both historical receipts retain their earlier meaning. Original failure output is retained; only the affected root suite is rerun.

The first delivered-starter fixture used macOS's /var alias. The initializer correctly refused a symlink-bearing input path before creation. The runner now supplies the resolved /private/var path; no product check was weakened and the failed disposable tree was removed.
