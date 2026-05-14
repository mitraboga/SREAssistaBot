# SRE Eval Harnesses

This folder contains lightweight benchmarks for SRE AssistaBot.

## SRE Quality And Hallucination Proxy

`run_sre_eval.py` calls the local ADK API, measures non-streaming `/run`
response latency, and scores responses with deterministic checks for SRE
structure, required terms, actionability, and unsupported live-data claims.

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
- hallucination proxy rate
- per-case missing required terms

The hallucination proxy rate is intentionally narrow: it flags claims that the
bot checked live logs, metrics, AWS, or Kubernetes data when no tool result was
provided. It is not a complete factuality benchmark.

## TTFT Probe

`run_ttft_probe.py` calls ADK's streaming `/run_sse` endpoint and measures time
to first streamed text.

```powershell
.\.venv\Scripts\python.exe -m evals.run_ttft_probe --api-url http://localhost:8001
```

## RAG Retrieval

`run_rag_eval.py` evaluates the local runbook and past-incident retriever.

```powershell
.\.venv\Scripts\python.exe -m evals.run_rag_eval
```

Metrics produced:

- Hit@1, Hit@3, Hit@5
- MRR
- citation precision@3 and precision@5
- average top relevant confidence

## Alert Deflection

`run_alert_eval.py` evaluates deterministic alert severity, page/ticket/dedupe
routing, known-issue matching, and PagerNoise reduction.

```powershell
.\.venv\Scripts\python.exe -m evals.run_alert_eval
```

Metrics produced:

- page decision accuracy
- severity accuracy
- known-issue hit rate
- alert deflection rate
- false escalation rate
- missed page rate
- PagerNoise reduction

The RAG and alert benchmarks use an expanded demo corpus and scenario set.
Expand the JSONL files further and replace the demo corpus with sanitized real
runbooks or incident records before presenting the numbers as production-grade
metrics.

Current expanded demo benchmark size:

- 20 SRE response-quality prompts
- 30 RAG retrieval queries
- 30 alert deflection scenarios
- 14 runbook documents
- 10 past-incident documents

The generated metrics are valid for this repository's demo/anonymized corpus.
They are not evidence of live production PagerDuty or incident-management
outcomes unless you evaluate against real historical data.
