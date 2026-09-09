# Active-root backend operating evidence

The bounded root pilot passed on the pinned local profile. Its corpus contained the root README and one accepted memory record: 2 source identities and 25 ready vector chunks. No existing product corpus was included.

Seven actual queries covered exact note/source lookup, conceptual note retrieval, and an absent exact identifier. Backend subprocess time ranged from 0.611 to 0.871 seconds (mean 0.756); parent call time, including current-source integrity checks, ranged from 0.657 to 0.918 seconds. Maximum query-worker RSS was 351,846,400 bytes. Two complete root index subprocesses took 2.256 and 2.289 seconds.

These are observed small-corpus measurements, not latency or memory guarantees. Each query used a fresh constrained process; the OS filesystem cache was not flushed. Other native agents were active on the host. The [isolated operating report](backend-operational-fit.md) records runtime/model sizes, versions, licenses, prerequisites and measurement limits.

The [root pilot](backend-root-results.json), [preservation inventory](backend-root-preservation.json), [compatibility decision](backend-compatibility-decision.json), and [public enablement/outage checks](root-backend-enablement-results.json) retain exact results. Root semantic use is enabled in current configuration, while the Template remains unprovisioned and backend-disabled.
