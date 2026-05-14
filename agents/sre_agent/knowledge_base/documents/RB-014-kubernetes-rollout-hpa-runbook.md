---
id: RB-014
title: Kubernetes Rollout And HPA Runbook
type: runbook
tags: kubernetes, rollout, hpa, deployment, autoscaling, readiness, replicas
---

# Kubernetes Rollout And HPA Runbook

Use this runbook when a Kubernetes rollout is stuck, replicas are unavailable,
or autoscaling is not keeping up with load.

## Read-Only Checks

1. Check deployment desired, updated, available, and unavailable replicas.
2. Check rollout status, ReplicaSet age, pod readiness, restarts, and events.
3. Inspect HPA current metrics, target utilization, scaling limits, and recent
   scale events.
4. Compare resource requests, limits, throttling, OOMKills, and node pressure.
5. Confirm readiness and liveness probe failures before restarting workloads.

## Mitigation Options

- Pause rollout or roll back only after confirming the new version is unhealthy.
- Raise HPA max replicas only after downstream capacity is verified.
- Fix probe configuration when healthy pods are being removed from service.

## Evidence To Cite

- Deployment replica health.
- HPA current versus target metrics.
- Pod readiness, events, and resource pressure.

