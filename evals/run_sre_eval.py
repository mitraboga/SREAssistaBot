"""Run a lightweight SRE quality and latency benchmark against the local ADK API."""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_API_URL = "http://localhost:8001"
DEFAULT_SCENARIOS = Path(__file__).with_name("sre_eval_scenarios.jsonl")
UNSUPPORTED_LIVE_CLAIMS = [
    "i checked",
    "i queried",
    "i executed",
    "logs confirm",
    "metrics confirm",
    "metrics prove",
    "cost explorer shows",
    "kubectl returned",
]


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                scenarios.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on {path}:{line_number}: {exc}") from exc
    return scenarios


def post_json(url: str, payload: dict[str, Any], timeout: int) -> Any:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"POST {url} failed with HTTP {exc.code}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"POST {url} failed: {exc}") from exc


def extract_response_text(data: Any) -> str:
    """Extract final text from common ADK event response shapes."""
    if isinstance(data, str):
        return data.strip()

    if isinstance(data, list):
        for item in reversed(data):
            text = extract_response_text(item)
            if text:
                return text
        return ""

    if not isinstance(data, dict):
        return ""

    content = data.get("content")
    if isinstance(content, dict):
        parts = content.get("parts")
        if isinstance(parts, list):
            texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
            joined = "\n".join(text for text in texts if text)
            if joined.strip():
                return joined.strip()

    for key in ["text", "response", "message", "content"]:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict | list):
            text = extract_response_text(value)
            if text:
                return text

    return ""


def count_hits(text_lower: str, terms: list[str]) -> tuple[list[str], list[str]]:
    hits = [term for term in terms if term.lower() in text_lower]
    missing = [term for term in terms if term.lower() not in text_lower]
    return hits, missing


def score_response(scenario: dict[str, Any], response_text: str) -> dict[str, Any]:
    text_lower = response_text.lower()
    required_terms = scenario.get("required_terms", [])
    expected_sections = scenario.get("expected_sections", [])
    action_terms = scenario.get("action_terms", [])
    forbidden_terms = scenario.get("forbidden_terms", [])

    required_hits, required_missing = count_hits(text_lower, required_terms)
    section_hits, section_missing = count_hits(text_lower, expected_sections)
    action_hits, _ = count_hits(text_lower, action_terms)
    forbidden_hits, _ = count_hits(text_lower, forbidden_terms)
    unsupported_hits, _ = count_hits(text_lower, UNSUPPORTED_LIVE_CLAIMS)

    required_rate = len(required_hits) / max(len(required_terms), 1)
    section_rate = len(section_hits) / max(len(expected_sections), 1)
    action_rate = min(len(action_hits) / max(min(len(action_terms), 4), 1), 1.0)
    unsupported_penalty = min(len(unsupported_hits) * 0.10, 0.30)
    forbidden_penalty = min(len(forbidden_hits) * 0.15, 0.45)

    quality_score = (
        (required_rate * 0.50)
        + (section_rate * 0.30)
        + (action_rate * 0.20)
        - unsupported_penalty
        - forbidden_penalty
    )
    quality_score = max(0.0, min(1.0, quality_score))

    min_score = float(scenario.get("min_score", 0.70))
    return {
        "quality_score": round(quality_score, 3),
        "passed": quality_score >= min_score and not forbidden_hits,
        "min_score": min_score,
        "required_hit_rate": round(required_rate, 3),
        "section_hit_rate": round(section_rate, 3),
        "action_hit_rate": round(action_rate, 3),
        "required_hits": required_hits,
        "required_missing": required_missing,
        "section_hits": section_hits,
        "section_missing": section_missing,
        "action_hits": action_hits,
        "forbidden_hits": forbidden_hits,
        "unsupported_live_claims": unsupported_hits,
        "word_count": len(response_text.split()),
    }


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = round((len(sorted_values) - 1) * pct)
    return sorted_values[index]


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [result["latency_seconds"] for result in results if result.get("ok")]
    scores = [
        result["score"]["quality_score"]
        for result in results
        if result.get("ok") and "score" in result
    ]
    passed = [result for result in results if result.get("score", {}).get("passed")]
    unsupported = [
        result
        for result in results
        if result.get("score", {}).get("unsupported_live_claims")
    ]

    unsupported_live_claim_rate = round(len(unsupported) / max(len(results), 1), 3)

    return {
        "case_count": len(results),
        "successful_api_calls": sum(1 for result in results if result.get("ok")),
        "pass_count": len(passed),
        "pass_rate": round(len(passed) / max(len(results), 1), 3),
        "average_latency_seconds": round(statistics.mean(latencies), 3) if latencies else 0.0,
        "p50_latency_seconds": round(percentile(latencies, 0.50), 3),
        "p95_latency_seconds": round(percentile(latencies, 0.95), 3),
        "average_quality_score": round(statistics.mean(scores), 3) if scores else 0.0,
        "unsupported_live_claim_rate": unsupported_live_claim_rate,
        "hallucination_proxy_rate": unsupported_live_claim_rate,
    }


def render_markdown(summary: dict[str, Any], results: list[dict[str, Any]]) -> str:
    lines = [
        "# SRE AssistaBot Eval Results",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Successful API calls: {summary['successful_api_calls']}",
        f"- Pass rate: {summary['pass_rate']:.1%}",
        f"- Average quality score: {summary['average_quality_score']:.3f}",
        f"- Average latency: {summary['average_latency_seconds']:.3f}s",
        f"- P50 latency: {summary['p50_latency_seconds']:.3f}s",
        f"- P95 latency: {summary['p95_latency_seconds']:.3f}s",
        f"- Unsupported live-claim rate: {summary['unsupported_live_claim_rate']:.1%}",
        f"- Hallucination proxy rate: {summary['hallucination_proxy_rate']:.1%}",
        "",
        "Note: latency is non-streaming `/run` response latency, not token-level TTFT.",
        "",
        "| Case | Category | Passed | Quality | Latency | Missing Required Terms |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for result in results:
        score = result.get("score", {})
        missing = ", ".join(score.get("required_missing", [])) or "-"
        lines.append(
            "| {id} | {category} | {passed} | {quality:.3f} | {latency:.3f}s | {missing} |".format(
                id=result["id"],
                category=result["category"],
                passed="yes" if score.get("passed") else "no",
                quality=score.get("quality_score", 0.0),
                latency=result.get("latency_seconds", 0.0),
                missing=missing.replace("|", "/"),
            )
        )

    return "\n".join(lines) + "\n"


def run_case(
    api_url: str,
    scenario: dict[str, Any],
    app_name: str,
    user_id: str,
    timeout: int,
) -> dict[str, Any]:
    safe_id = scenario["id"].replace(" ", "_")
    session_id = f"eval_{safe_id}_{int(time.time() * 1000)}"

    start = time.perf_counter()
    post_json(
        f"{api_url}/apps/{app_name}/users/{user_id}/sessions/{session_id}",
        {"state": {"eval_case_id": scenario["id"], "category": scenario["category"]}},
        timeout=timeout,
    )
    session_created = time.perf_counter()

    raw_response = post_json(
        f"{api_url}/run",
        {
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id,
            "new_message": {"role": "user", "parts": [{"text": scenario["prompt"]}]},
        },
        timeout=timeout,
    )
    end = time.perf_counter()

    response_text = extract_response_text(raw_response)
    score = score_response(scenario, response_text)

    return {
        "id": scenario["id"],
        "category": scenario["category"],
        "ok": True,
        "session_create_seconds": round(session_created - start, 3),
        "latency_seconds": round(end - session_created, 3),
        "total_seconds": round(end - start, 3),
        "score": score,
        "prompt": scenario["prompt"],
        "response_text": response_text,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SRE AssistaBot eval scenarios.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--output-dir", type=Path, default=Path("evals/results"))
    parser.add_argument("--app-name", default="sre_agent")
    parser.add_argument("--user-id", default="u_eval_runner")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--limit", type=int, default=0, help="Limit number of scenarios.")
    args = parser.parse_args()

    scenarios = load_scenarios(args.scenarios)
    if args.limit:
        scenarios = scenarios[: args.limit]

    results: list[dict[str, Any]] = []
    for scenario in scenarios:
        print(f"Running {scenario['id']}...")
        try:
            result = run_case(
                api_url=args.api_url.rstrip("/"),
                scenario=scenario,
                app_name=args.app_name,
                user_id=args.user_id,
                timeout=args.timeout,
            )
        except Exception as exc:
            result = {
                "id": scenario["id"],
                "category": scenario["category"],
                "ok": False,
                "error": str(exc),
                "latency_seconds": 0.0,
                "score": {
                    "quality_score": 0.0,
                    "passed": False,
                    "required_missing": scenario.get("required_terms", []),
                },
            }
        results.append(result)

    summary = summarize(results)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    json_path = args.output_dir / f"sre_eval_{timestamp}.json"
    markdown_path = args.output_dir / f"sre_eval_{timestamp}.md"
    payload = {
        "generated_at": timestamp,
        "api_url": args.api_url,
        "summary": summary,
        "results": results,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(summary, results), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")

    return 0 if summary["pass_rate"] >= 0.70 else 1


if __name__ == "__main__":
    raise SystemExit(main())
