import { useEffect, useRef, useState } from "react";
import { ArrowRight, CheckCheck, Radio, ShieldAlert } from "lucide-react";
import { Badge, ErrorNotice, SourceLink } from "../components/ui";
import { liveApi } from "../lib/api";
import { demoClassify } from "../lib/demo";
import { useWorkspace } from "../lib/workspace";
import type { AlertInput, AlertResult } from "../lib/types";

const samples = [
  {
    title: "Customer-impacting errors",
    alert_text:
      "Checkout 5xx payment failures in NA with customer complaints after deployment.",
    service: "checkout-api",
    current_severity: "P2",
  },
  {
    title: "Recurring nightly noise",
    alert_text:
      "Nightly checkout latency alert is self-resolving with no customer impact.",
    service: "checkout-api",
    current_severity: "P4",
  },
];
const routeLabels: Record<string, string> = {
  page_oncall: "Page on-call",
  dedupe_known_issue: "Review known issue",
  ticket: "Create a ticket",
  watch: "Watch & investigate",
};

export function Triage() {
  const { mode } = useWorkspace();
  const [input, setInput] = useState<AlertInput>({
    alert_text: "",
    service: "",
    current_severity: "",
  });
  const [result, setResult] = useState<AlertResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const controller = useRef<AbortController | null>(null);
  useEffect(
    () => () => {
      controller.current?.abort();
      controller.current = null;
    },
    [],
  );
  function update(next: AlertInput) {
    setInput(next);
    setResult(null);
    setError("");
  }
  async function classify() {
    if (controller.current || !input.alert_text.trim()) return;
    const current = new AbortController();
    controller.current = current;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const data =
        mode === "demo"
          ? demoClassify(input)
          : await liveApi.classify(input, current.signal);
      if (controller.current === current) setResult(data);
    } catch (failure) {
      if (controller.current === current)
        setError(
          failure instanceof Error ? failure.message : "Classification failed.",
        );
    } finally {
      if (controller.current === current) {
        controller.current = null;
        setBusy(false);
      }
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">A QUIETER, CLEARER SIGNAL</p>
          <h1>Alert triage</h1>
          <p>
            Review the severity, routing recommendation, and related evidence.
          </p>
        </div>
        <Badge tone="neutral">Recommendations only</Badge>
      </div>
      <div className="triage-grid">
        <section className="panel triage-input">
          <div className="panel-heading">
            <h2>
              <Radio size={18} />
              Inspect an alert
            </h2>
          </div>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void classify();
            }}
          >
            <label>
              Alert description
              <textarea
                required
                disabled={busy}
                maxLength={10000}
                rows={7}
                value={input.alert_text}
                onChange={(event) =>
                  update({ ...input, alert_text: event.target.value })
                }
                placeholder="Paste the alert text, symptoms, and customer impact…"
              />
            </label>
            <div className="form-grid">
              <label>
                Service
                <input
                  disabled={busy}
                  maxLength={120}
                  value={input.service}
                  onChange={(event) =>
                    update({ ...input, service: event.target.value })
                  }
                  placeholder="e.g. checkout-api"
                />
              </label>
              <label>
                Incoming severity
                <select
                  disabled={busy}
                  value={input.current_severity}
                  onChange={(event) =>
                    update({ ...input, current_severity: event.target.value })
                  }
                >
                  <option value="">Unknown</option>
                  {["P1", "P2", "P3", "P4"].map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
            </div>
            {error && <ErrorNotice message={error} />}
            <button
              type="submit"
              className="primary full-width"
              disabled={busy || !input.alert_text.trim()}
            >
              {busy ? <span className="spinner" /> : <ShieldAlert size={16} />}
              {busy ? "Classifying…" : "Review routing"}
              <ArrowRight size={15} />
            </button>
          </form>
          <div className="sample-alerts">
            <p className="eyebrow">TRY A SCENARIO</p>
            {samples.map((sample) => (
              <button
                disabled={busy}
                className="sample-button"
                key={sample.title}
                onClick={() =>
                  update({
                    alert_text: sample.alert_text,
                    service: sample.service,
                    current_severity: sample.current_severity,
                  })
                }
              >
                {sample.title}
                <ArrowRight size={14} />
              </button>
            ))}
          </div>
        </section>
        <section
          className="panel triage-result"
          aria-label="Alert recommendation"
          aria-live="polite"
        >
          <div className="panel-heading">
            <h2>Routing recommendation</h2>
            {result && (
              <Badge tone={mode === "demo" ? "neutral" : "green"}>
                {mode === "demo" ? "Demo classifier" : "Backend classifier"}
              </Badge>
            )}
          </div>
          {result ? (
            <div className="routing-content">
              <div
                className={`route-hero ${result.should_page ? "page" : "quiet"}`}
              >
                <span className="route-icon">
                  {result.should_page ? (
                    <ShieldAlert size={26} />
                  ) : (
                    <CheckCheck size={26} />
                  )}
                </span>
                <Badge tone={result.recommended_severity.toLowerCase()}>
                  {result.recommended_severity}
                </Badge>
                <h2>
                  {routeLabels[result.recommended_route] ||
                    result.recommended_route}
                </h2>
                <p>{result.reason}</p>
              </div>
              <dl className="routing-details">
                <dt>Classifier score</dt>
                <dd>{Math.round(result.confidence * 100)}%</dd>
                <dt>Dedupe key</dt>
                <dd className="mono">{result.dedupe_key}</dd>
              </dl>
              <p className="muted small">
                Heuristic confidence, not a calibrated probability. Confirm
                impact before acting.
              </p>
              {result.known_issue && (
                <div className="known-issue">
                  <p className="eyebrow">RELATED KNOWLEDGE</p>
                  <h3>{result.known_issue.title}</h3>
                  <p>{result.known_issue.snippet}</p>
                  <SourceLink id={result.known_issue.source_id}>
                    Read {result.known_issue.citation}
                  </SourceLink>
                </div>
              )}
              <div className="next-checks">
                <h3>Before taking action</h3>
                <ul>
                  {result.next_checks.map((check) => (
                    <li key={check}>
                      <CheckCheck size={15} />
                      {check}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="empty-state triage-empty">
              <span className="welcome-icon">
                <Radio size={28} />
              </span>
              <h2>Make the signal actionable.</h2>
              <p>
                Enter an alert to see its recommended route,
                <br />
                severity, and related runbook.
              </p>
              <div className="route-preview">
                <Badge tone="p2">Page</Badge>
                <ArrowRight size={14} />
                <Badge tone="p3">Ticket</Badge>
                <ArrowRight size={14} />
                <Badge tone="green">Known issue</Badge>
              </div>
            </div>
          )}
        </section>
      </div>
      <p className="footnote">
        This interface does not send pages, create external tickets, or change
        infrastructure.
      </p>
    </>
  );
}
