---
id: PI-006
title: Past Incident - Login Failures From Token Refresh Errors
type: past_incident
tags: auth, login, token, refresh, oauth, 401, identity-provider
---

# Past Incident - Login Failures From Token Refresh Errors

Users were logged out repeatedly after a token refresh configuration change.
401 responses increased, but core API availability stayed healthy.

## What Helped

- Separating login success rate from API availability kept triage focused.
- OAuth callback latency was normal, but token refresh errors spiked.
- Reverting the refresh-token audience setting restored sessions.

## Follow-Up Actions

- Add token refresh error alerts.
- Include auth config diffs in release notes.
- Add synthetic login checks for each identity provider.

