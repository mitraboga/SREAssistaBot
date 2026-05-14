# SRE Eval Harness

This folder contains a lightweight benchmark for SRE AssistaBot.

The harness calls the local ADK API, measures non-streaming `/run` response
latency, and scores responses with deterministic checks for SRE structure,
required terms, actionability, and unsupported live-data claims.

Run against the local agent API:

```powershell
.\.venv\Scripts\python.exe -m evals.run_sre_eval --api-url http://localhost:8001
```

Run a smaller smoke test:

```powershell
.\.venv\Scripts\python.exe -m evals.run_sre_eval --limit 3
```

Generated results are written under `evals/results/` and are intentionally not
committed.

Metrics produced:

- pass rate
- average quality score
- average latency
- p50 latency
- p95 latency
- unsupported live-claim rate
- per-case missing required terms

This is not a RAG benchmark yet. Hit@K, MRR, citation accuracy, and retrieval
groundedness require a runbook/past-incident corpus and retrieval pipeline.
