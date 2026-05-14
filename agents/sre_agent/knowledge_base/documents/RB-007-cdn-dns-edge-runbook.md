---
id: RB-007
title: CDN DNS And Edge Outage Runbook
type: runbook
tags: cdn, dns, cloudfront, route53, waf, cache, edge, 403, 404, tls
---

# CDN DNS And Edge Outage Runbook

Use this runbook when users report regional reachability issues, stale content,
TLS errors, 403/404 responses at the edge, or DNS resolution failures.

## Read-Only Checks

1. Compare browser errors, CDN 4xx/5xx, origin 5xx, and DNS lookup failures by
   region and ISP.
2. Verify DNS records, TTL, hosted zone changes, certificate validity, and
   propagation timing.
3. Check CDN cache behavior, origin routing, WAF blocks, signed URL policies,
   and recent invalidations.
4. Confirm whether origin is healthy before purging cache or changing DNS.

## Mitigation Options

- Revert the most recent cache behavior or WAF rule.
- Fail over DNS only after confirming origin readiness.
- Invalidate a narrow path if stale or poisoned content is isolated.

## Evidence To Cite

- CDN status codes and cache result type.
- DNS records and TTL.
- WAF rule matches.
- Origin health and regional error split.

