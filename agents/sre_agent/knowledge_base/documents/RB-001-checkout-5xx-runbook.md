---
id: RB-001
title: Checkout 5xx And Payment Failure Runbook
type: runbook
tags: checkout, payments, 5xx, api-gateway, postgres, na
---

# Checkout 5xx And Payment Failure Runbook

Use this runbook when checkout has elevated 5xx errors, payment failures, cart
abandonment, or customer complaints.

## First 15 Minutes

1. Confirm impact from read-only dashboards: checkout request rate, 5xx rate,
   payment authorization failures, latency, and regional split.
2. Compare the incident window against the most recent deploy, feature flag
   change, dependency status, and API gateway errors.
3. Check payment provider timeout and decline-code distribution before assuming
   the database is the cause.
4. Inspect Postgres saturation signals: connection count, lock waits, slow
   queries, CPU, storage latency, and connection pool exhaustion.
5. Escalate to payments, database, and platform owners if customer-impacting
   errors continue for more than one alert window.

## Rollback Criteria

Rollback or disable the latest checkout/payment change when error rate or
payment failure rate remains elevated after mitigation, and when the change is
within the incident window.

## Evidence To Cite

- API gateway 5xx and p95/p99 latency.
- Payment authorization failures and provider timeouts.
- Postgres connection pool, lock waits, and slow query samples.
- Deploy and feature-flag timeline.

