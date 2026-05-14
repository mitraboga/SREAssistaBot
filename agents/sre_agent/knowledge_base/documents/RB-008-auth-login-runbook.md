---
id: RB-008
title: Authentication And Login Degradation Runbook
type: runbook
tags: auth, login, oauth, oidc, token, session, 401, 403, identity
---

# Authentication And Login Degradation Runbook

Use this runbook when login, session refresh, OAuth/OIDC callback, or token
validation paths fail.

## Read-Only Checks

1. Check login success rate, 401/403 rate, token refresh errors, callback
   latency, and identity-provider status.
2. Compare failures by client, region, identity provider, and application
   version.
3. Verify certificate rotation, JWKS cache age, redirect URI config, clock skew,
   and session store saturation.
4. Confirm whether retries are creating duplicate login attempts or account
   lockouts.

## Mitigation Options

- Roll back auth config or feature flag changes.
- Reduce JWKS cache TTL only if key rotation evidence supports it.
- Route users to a fallback identity provider if that path is tested.

## Evidence To Cite

- Login success and token refresh error rates.
- Identity provider status and callback latency.
- JWKS, certificate, redirect URI, and clock-skew checks.

