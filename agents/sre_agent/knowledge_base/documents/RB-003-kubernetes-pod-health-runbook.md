---
id: RB-003
title: Kubernetes Pod Health Runbook
type: runbook
tags: kubernetes, pods, crashloopbackoff, rollout, node-pressure, kubectl
---

# Kubernetes Pod Health Runbook

Use this runbook when pods are unhealthy, deployments are stuck, or node
pressure may be affecting workloads.

## Read-Only Checks

1. Run `kubectl get pods` with namespace and label selectors to identify pod
   phase, restarts, readiness, and age.
2. Run `kubectl describe pod` for events such as image pull failures, failed
   probes, OOMKilled, and scheduling issues.
3. Run `kubectl logs --tail` for recent application errors without changing
   workload state.
4. Run `kubectl rollout status deployment/<name>` and compare desired,
   updated, available, and unavailable replicas.
5. Run `kubectl describe node` when pods are pending or evicted and check CPU,
   memory, disk, and PID pressure.

## Evidence To Cite

- Pod phase and restart count.
- CrashLoopBackOff, OOMKilled, probe failure, or scheduling event.
- Deployment replica health.
- Node pressure condition.

