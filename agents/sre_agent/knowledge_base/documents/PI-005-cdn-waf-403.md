---
id: PI-005
title: Past Incident - CDN WAF Rule Caused Regional 403 Errors
type: past_incident
tags: cdn, waf, cloudfront, 403, edge, regional
---

# Past Incident - CDN WAF Rule Caused Regional 403 Errors

A WAF rule change blocked valid checkout traffic from one region and produced a
spike in CDN 403 responses while origin health remained normal.

## What Helped

- CDN logs showed 403s at the edge, not origin 5xx responses.
- WAF sampled requests matched the new managed rule.
- Reverting the WAF rule resolved the regional impact.

## Follow-Up Actions

- Add regional CDN 4xx dashboards.
- Require sampled request review before WAF rule rollout.
- Add an owner to edge configuration changes.

