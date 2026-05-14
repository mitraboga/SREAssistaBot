"""Evaluate deterministic alert deflection and pager-noise metrics."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.sre_agent.tools.alert_intelligence import classify_alert_for_escalation


DEFAULT_SCENARIOS = Path(__file__).with_name("alert_eval_scenarios.jsonl")


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


def score_case(case: dict[str, Any]) -> dict[str, Any]:
    decision = classify_alert_for_escalation(
        alert_text=case["alert_text"],
        service=case.get("service", ""),
        current_severity=case.get("current_severity", ""),
    )
    known_issue_found = bool(decision.get("known_issue"))
    page_correct = decision["should_page"] is case["expected_should_page"]
    severity_correct = decision["recommended_severity"] == case["expected_severity"]
    known_issue_correct = known_issue_found is case.get("expected_known_issue", False)

    return {
        "id": case["id"],
        "alert_text": case["alert_text"],
        "expected_should_page": case["expected_should_page"],
        "predicted_should_page": decision["should_page"],
        "expected_severity": case["expected_severity"],
        "predicted_severity": decision["recommended_severity"],
        "expected_known_issue": case.get("expected_known_issue", False),
        "known_issue_found": known_issue_found,
        "baseline_should_page": case.get("baseline_should_page", True),
        "page_correct": page_correct,
        "severity_correct": severity_correct,
        "known_issue_correct": known_issue_correct,
        "decision": decision,
    }


def _rate(count: int, total: int) -> float:
    return round(count / max(total, 1), 3)


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_pages = sum(1 for result in results if result["baseline_should_page"])
    predicted_pages = sum(1 for result in results if result["predicted_should_page"])
    expected_pages = sum(1 for result in results if result["expected_should_page"])
    expected_non_pages = len(results) - expected_pages
    false_escalations = sum(
        1
        for result in results
        if result["predicted_should_page"] and not result["expected_should_page"]
    )
    missed_pages = sum(
        1
        for result in results
        if not result["predicted_should_page"] and result["expected_should_page"]
    )
    expected_known = [result for result in results if result["expected_known_issue"]]
    known_hits = sum(1 for result in expected_known if result["known_issue_found"])

    return {
        "case_count": len(results),
        "page_decision_accuracy": _rate(sum(1 for result in results if result["page_correct"]), len(results)),
        "severity_accuracy": _rate(sum(1 for result in results if result["severity_correct"]), len(results)),
        "known_issue_hit_rate": _rate(known_hits, len(expected_known)),
        "alert_deflection_rate": _rate(
            sum(1 for result in results if not result["predicted_should_page"]),
            len(results),
        ),
        "false_escalation_rate": _rate(false_escalations, expected_non_pages),
        "missed_page_rate": _rate(missed_pages, expected_pages),
        "baseline_pages": baseline_pages,
        "predicted_pages": predicted_pages,
        "pager_noise_reduction": round(
            (baseline_pages - predicted_pages) / max(baseline_pages, 1),
            3,
        ),
    }


def render_markdown(summary: dict[str, Any], results: list[dict[str, Any]]) -> str:
    lines = [
        "# Alert Deflection Eval Results",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Page decision accuracy: {summary['page_decision_accuracy']:.1%}",
        f"- Severity accuracy: {summary['severity_accuracy']:.1%}",
        f"- Known-issue hit rate: {summary['known_issue_hit_rate']:.1%}",
        f"- Alert deflection rate: {summary['alert_deflection_rate']:.1%}",
        f"- False escalation rate: {summary['false_escalation_rate']:.1%}",
        f"- Missed page rate: {summary['missed_page_rate']:.1%}",
        f"- PagerNoise reduction: {summary['pager_noise_reduction']:.1%}",
        "",
        "| Case | Page Correct | Severity Correct | Predicted Route | Known Issue |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in results:
        known_issue = result["decision"].get("known_issue") or {}
        lines.append(
            "| {id} | {page} | {severity} | {route} | {known} |".format(
                id=result["id"],
                page="yes" if result["page_correct"] else "no",
                severity="yes" if result["severity_correct"] else "no",
                route=result["decision"]["recommended_route"],
                known=known_issue.get("source_id", "-"),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run alert deflection evals.")
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--output-dir", type=Path, default=Path("evals/results"))
    args = parser.parse_args()

    cases = load_jsonl(args.scenarios)
    results = [score_case(case) for case in cases]
    summary = summarize(results)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"alert_eval_{timestamp}.json"
    markdown_path = args.output_dir / f"alert_eval_{timestamp}.md"
    payload = {"generated_at": timestamp, "summary": summary, "results": results}
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(summary, results), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")

    return 0 if summary["page_decision_accuracy"] >= 0.85 and summary["missed_page_rate"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

