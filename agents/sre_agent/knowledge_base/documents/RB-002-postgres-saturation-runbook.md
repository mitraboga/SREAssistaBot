---
id: RB-002
title: Postgres Saturation Runbook
type: runbook
tags: postgres, database, saturation, connections, locks, slow-query
---

# Postgres Saturation Runbook

Use this runbook when a service backed by Postgres shows elevated latency,
timeouts, connection errors, or queueing.

## Read-Only Checks

1. Check active connections, connection pool saturation, and wait events.
2. Review slow queries, lock waits, deadlocks, and long-running transactions.
3. Compare database CPU, memory, IOPS, storage latency, and replica lag against
   the previous healthy baseline.
4. Confirm whether application retries are amplifying database load.
5. Check whether a deploy introduced a query-plan regression or missing index.

## Mitigation Options

- Shed non-critical traffic or disable expensive optional paths.
- Increase connection pool backpressure before scaling application pods.
- Roll back the deploy that introduced the query regression.
- Add a targeted index only after validating plan impact outside the hot path.

## Evidence To Cite

- Connection pool utilization.
- Query latency percentiles and slow-query examples.
- Lock wait and transaction age.
- Database CPU, IOPS, storage latency, and replica lag.

