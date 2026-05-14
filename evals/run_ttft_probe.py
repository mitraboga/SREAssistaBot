"""Probe token-level TTFT through ADK's `/run_sse` endpoint."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evals.run_sre_eval import extract_response_text


DEFAULT_API_URL = "http://localhost:8001"


def post_json(url: str, payload: dict[str, Any], timeout: int) -> Any:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def parse_sse_data(line: bytes) -> dict[str, Any] | None:
    decoded = line.decode("utf-8", errors="replace").strip()
    if not decoded.startswith("data:"):
        return None
    payload = decoded.removeprefix("data:").strip()
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {"raw": payload}


def event_has_text(event: dict[str, Any]) -> bool:
    if event.get("error"):
        return False
    return bool(extract_response_text(event))


def probe_ttft(
    api_url: str,
    prompt: str,
    app_name: str,
    user_id: str,
    timeout: int,
) -> dict[str, Any]:
    session_id = f"ttft_eval_{int(time.time() * 1000)}"
    api_url = api_url.rstrip("/")

    post_json(
        f"{api_url}/apps/{app_name}/users/{user_id}/sessions/{session_id}",
        {"state": {"eval": "ttft_probe"}},
        timeout=timeout,
    )

    payload = {
        "app_name": app_name,
        "user_id": user_id,
        "session_id": session_id,
        "streaming": True,
        "new_message": {"role": "user", "parts": [{"text": prompt}]},
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{api_url}/run_sse",
        data=data,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )

    start = time.perf_counter()
    first_event_seconds: float | None = None
    first_text_seconds: float | None = None
    final_text = ""
    event_count = 0
    error_event = ""

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for line in response:
                event = parse_sse_data(line)
                if event is None:
                    continue
                event_count += 1
                now = time.perf_counter()
                if first_event_seconds is None:
                    first_event_seconds = now - start
                if event.get("error"):
                    error_event = str(event["error"])
                    break
                event_text = extract_response_text(event)
                if event_text:
                    final_text = event_text
                    if first_text_seconds is None:
                        first_text_seconds = now - start
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "status": "error",
            "message": f"HTTP {exc.code}: {body[:500]}",
            "event_count": event_count,
        }
    except urllib.error.URLError as exc:
        return {"status": "error", "message": str(exc), "event_count": event_count}

    total_seconds = time.perf_counter() - start
    status = "success" if first_text_seconds is not None and not error_event else "unsupported"
    message = (
        "Streaming text observed."
        if status == "success"
        else "No text event observed from /run_sse; provider or ADK route may be non-streaming."
    )
    if error_event:
        message = f"SSE returned model error: {error_event[:300]}"

    return {
        "status": status,
        "message": message,
        "event_count": event_count,
        "first_event_seconds": round(first_event_seconds or 0.0, 3),
        "ttft_seconds": round(first_text_seconds or 0.0, 3),
        "total_seconds": round(total_seconds, 3),
        "final_word_count": len(final_text.split()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe ADK SSE TTFT.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--app-name", default="sre_agent")
    parser.add_argument("--user-id", default="u_ttft_probe")
    parser.add_argument(
        "--prompt",
        default="Create a concise incident brief for checkout 5xx and payment failures.",
    )
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--output-dir", type=Path, default=Path("evals/results"))
    args = parser.parse_args()

    result = probe_ttft(
        api_url=args.api_url,
        prompt=args.prompt,
        app_name=args.app_name,
        user_id=args.user_id,
        timeout=args.timeout,
    )
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"ttft_probe_{timestamp}.json"
    json_path.write_text(
        json.dumps({"generated_at": timestamp, "result": result}, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))
    print(f"Wrote {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

