---
id: PI-004
title: Past Incident - Bad Kubernetes Rollout From Readiness Probe Failure
type: past_incident
tags: kubernetes, rollout, readiness, deployment, pods, 5xx
---

# Past Incident - Bad Kubernetes Rollout From Readiness Probe Failure

A checkout deployment rolled out with a readiness probe path that returned 500
for the new version. The service had reduced capacity and intermittent 5xx
responses.

## What Helped

- Rollout status showed unavailable replicas during the incident window.
- Pod events showed repeated readiness probe failures.
- Rolling back the deployment restored available replicas.

## Follow-Up Actions

- Add readiness probe checks to pre-deploy validation.
- Alert on unavailable replicas during canary rollout.
- Include deployment version in incident dashboards.

