"""Evaluate local runbook and past-incident retrieval metrics."""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.sre_agent.tools.knowledge_base import retrieve_documents


DEFAULT_QUERIES = Path(__file__).with_name("rag_eval_queries.jsonl")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on {path}:{line_number}: {exc}") from exc
    return rows


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for index, source_id in enumerate(retrieved_ids, start=1):
        if source_id in relevant_ids:
            return 1.0 / index
    return 0.0


def score_query(case: dict[str, Any], top_k: int) -> dict[str, Any]:
    results = retrieve_documents(case["query"], top_k=top_k)
    retrieved_ids = [result["source_id"] for result in results]
    relevant_ids = set(case["relevant_ids"])
    relevant_retrieved = [source_id for source_id in retrieved_ids if source_id in relevant_ids]
    relevant_confidences = [
        result["confidence"] for result in results if result["source_id"] in relevant_ids
    ]

    return {
        "id": case["id"],
        "query": case["query"],
        "relevant_ids": sorted(relevant_ids),
        "retrieved_ids": retrieved_ids,
        "citations": [result["citation"] for result in results],
        "hit_at_1": bool(set(retrieved_ids[:1]) & relevant_ids),
        "hit_at_3": bool(set(retrieved_ids[:3]) & relevant_ids),
        "hit_at_5": bool(set(retrieved_ids[:5]) & relevant_ids),
        "reciprocal_rank": round(reciprocal_rank(retrieved_ids, relevant_ids), 3),
        "citation_precision_at_3": round(len(set(retrieved_ids[:3]) & relevant_ids) / 3, 3),
        "citation_precision_at_5": round(len(set(retrieved_ids[:5]) & relevant_ids) / 5, 3),
        "matched_relevant_ids": sorted(set(relevant_retrieved)),
        "top_relevant_confidence": round(max(relevant_confidences), 3)
        if relevant_confidences
        else 0.0,
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "case_count": len(results),
        "hit_at_1": round(sum(1 for result in results if result["hit_at_1"]) / max(len(results), 1), 3),
        "hit_at_3": round(sum(1 for result in results if result["hit_at_3"]) / max(len(results), 1), 3),
        "hit_at_5": round(sum(1 for result in results if result["hit_at_5"]) / max(len(results), 1), 3),
        "mrr": round(statistics.mean(result["reciprocal_rank"] for result in results), 3)
        if results
        else 0.0,
        "citation_precision_at_3": round(
            statistics.mean(result["citation_precision_at_3"] for result in results), 3
        )
        if results
        else 0.0,
        "citation_precision_at_5": round(
            statistics.mean(result["citation_precision_at_5"] for result in results), 3
        )
        if results
        else 0.0,
        "average_top_relevant_confidence": round(
            statistics.mean(result["top_relevant_confidence"] for result in results), 3
        )
        if results
        else 0.0,
    }


def render_markdown(summary: dict[str, Any], results: list[dict[str, Any]]) -> str:
    lines = [
        "# RAG Retrieval Eval Results",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Hit@1: {summary['hit_at_1']:.1%}",
        f"- Hit@3: {summary['hit_at_3']:.1%}",
        f"- Hit@5: {summary['hit_at_5']:.1%}",
        f"- MRR: {summary['mrr']:.3f}",
        f"- Citation precision@3: {summary['citation_precision_at_3']:.3f}",
        f"- Citation precision@5: {summary['citation_precision_at_5']:.3f}",
        f"- Average top relevant confidence: {summary['average_top_relevant_confidence']:.3f}",
        "",
        "| Case | Hit@3 | Relevant | Retrieved | Citations |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append(
            "| {id} | {hit} | {relevant} | {retrieved} | {citations} |".format(
                id=result["id"],
                hit="yes" if result["hit_at_3"] else "no",
                relevant=", ".join(result["relevant_ids"]),
                retrieved=", ".join(result["retrieved_ids"]),
                citations=", ".join(result["citations"]),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local RAG retrieval evals.")
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, default=Path("evals/results"))
    args = parser.parse_args()

    cases = load_jsonl(args.queries)
    results = [score_query(case, top_k=args.top_k) for case in cases]
    summary = summarize(results)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"rag_eval_{timestamp}.json"
    markdown_path = args.output_dir / f"rag_eval_{timestamp}.md"
    payload = {"generated_at": timestamp, "summary": summary, "results": results}
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(summary, results), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")

    return 0 if summary["hit_at_3"] >= 0.80 and summary["mrr"] >= 0.60 else 1


if __name__ == "__main__":
    raise SystemExit(main())

