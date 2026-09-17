# Workbench public-entry repair

The bounded source repair is complete and frozen for host adoption. Cross-site GET requests can reach only the exact public `/` or `/index.html` shell when Fetch Metadata says `navigate` and `document`. No query variant is included. The exception does not require `Sec-Fetch-User`: user activation is distinct from navigation mode and is absent for unactivated navigation requests. [W3C Fetch Metadata, sections 2.1–2.4](https://www.w3.org/TR/fetch-metadata/).

Exact Host and supplied Origin checks run before this exception. Cross-site health, assets, APIs, iframe/subresource requests and POST session exchange remain rejected. Authentication, one-use bootstrap tokens, session expiry, CSRF, cookies, CORS, request bounds and authoring authority are unchanged.

The focused HTTP security suite passed **10 tests in 10.299 seconds**. It includes activated/unactivated shell entry and reload, direct/no-metadata/none/same-origin entry, query/non-shell/iframe/subresource rejection, bad Host/Origin, cross-site session and authenticated API requests, bootstrap replay/expiry, CSRF, cookie isolation and existing authoring protections. The command and raw result are in `verification.json` and `security-tests.txt`. These are disposable actual HTTP-service tests; host browser navigation remains a separate observation.

Exactly four reusable files changed: the workbench helper, its existing security test file, the current v12 inventory's one workbench hash, and the current `INVENTORY_SHA256` constant. Exact preimages and diffs are retained. Historical v11 inventory and its legacy pin remain unchanged. The supported Template updater applied those four mapped changes; reopened check reports current, 427 managed / 420 source files, no conflicts. The initializer's read-only current-v12 `template_sources` check validated the complete 427-file starter closure.

Forty protected hashes were reopened unchanged, including the installed root helper, complete root v9 initializer package, historical inventory, configurations, registry and all five final reports. No active root helper, service, browser UI, Task, plan, memory or product project was changed by this repair.

The host's only proposed root adoption is `.agents/skills/ontology/scripts/ontology_workbench.py`:

- Expected installed predecessor: `9b75ffd7e58b61c0f67f77bb809ce571a89659f262a22725581552fa973a5bc7`
- Reviewed new source: `1a02494a3bbe9979f48a152527fd0b1c6a566bc53576665822aa7fc34a11318e`

Use `root-adoption-manifest.json`. The host stops the exact existing service, reopens the two hashes, adopts the one helper and restarts through the existing owner route before observing authenticated browser navigation. This handoff does not claim root adoption or browser acceptance. All source writes are stopped; no command remains active.
