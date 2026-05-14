---
id: RB-010
title: Redis Cache Degradation Runbook
type: runbook
tags: redis, cache, memory, eviction, connection, timeout, hot-key, latency
---

# Redis Cache Degradation Runbook

Use this runbook when cache latency, Redis timeouts, evictions, connection
errors, or hot-key behavior affect application performance.

## Read-Only Checks

1. Check Redis CPU, memory, maxmemory policy, evictions, fragmentation, and
   connection count.
2. Compare command latency, slowlog, timeout rate, and network errors.
3. Look for hot keys, cache stampede, high cardinality keys, and TTL changes.
4. Verify whether database load increased because cache hit rate dropped.

## Mitigation Options

- Add request coalescing or jittered TTL for stampede patterns.
- Increase connection pooling backpressure before scaling clients.
- Roll back cache key or TTL changes that match the incident window.

## Evidence To Cite

- Cache hit rate and Redis command latency.
- Evictions, memory pressure, and connection count.
- Database load after cache miss increase.

