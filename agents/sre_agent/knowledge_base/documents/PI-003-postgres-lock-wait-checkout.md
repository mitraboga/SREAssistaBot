---
id: PI-003
title: Past Incident - Checkout Slowness From Postgres Lock Waits
type: past_incident
tags: checkout, postgres, lock-wait, slow-query, database, latency
---

# Past Incident - Checkout Slowness From Postgres Lock Waits

Checkout latency increased after a schema migration left a transaction open.
Application retries amplified connection pool pressure.

## What Helped

- Lock wait and transaction age dashboards identified the blocked table.
- Read-only query samples showed checkout requests waiting on the same lock.
- Rollback was avoided after the migration was completed safely.

## Follow-Up Actions

- Add migration lock-time alerts.
- Require migration dry runs for checkout tables.
- Add retry budgets so database saturation is not amplified.

