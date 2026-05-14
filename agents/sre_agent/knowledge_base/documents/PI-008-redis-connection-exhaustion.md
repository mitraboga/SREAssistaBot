---
id: PI-008
title: Past Incident - Redis Connection Exhaustion Caused API Latency
type: past_incident
tags: redis, cache, connection, timeout, latency, api
---

# Past Incident - Redis Connection Exhaustion Caused API Latency

API latency increased when a client release opened too many Redis connections.
Cache timeouts caused fallback reads against Postgres.

## What Helped

- Redis connection count and command timeout rate rose before API p99 latency.
- Postgres read load increased after cache hit rate fell.
- Rolling back the client connection-pool change restored cache stability.

## Follow-Up Actions

- Add client-side connection limits.
- Alert on cache timeout rate and hit-rate drop.
- Include Redis connection count in API latency triage.

