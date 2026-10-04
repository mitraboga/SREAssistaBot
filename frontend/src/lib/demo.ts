import corpus from "./demo-corpus.json";
import type {
  AlertInput,
  AlertResult,
  Incident,
  KnowledgeDocument,
  SearchResult,
} from "./types";

// Snapshot of the repository's anonymized runbooks; no network or model calls.
export const demoDocuments: KnowledgeDocument[] = corpus;

export function demoSearch(query: string): SearchResult[] {
  const words = query.toLowerCase().match(/[a-z0-9-]{2,}/g) || [];
  return demoDocuments
    .map((document) => ({
      document,
      score: words.reduce(
        (sum, word) =>
          sum +
          (`${document.title} ${document.tags.join(" ")} ${document.body}`
            .toLowerCase()
            .includes(word)
            ? 1
            : 0),
        0,
      ),
    }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map(({ document, score }, index) => ({
      ...document,
      citation: `[${document.source_id}]`,
      confidence: score / Math.max(words.length, 1),
      rank: index + 1,
      snippet: document.body
        .replace(/^#{1,6}\s+.*$/gm, "")
        .replace(/\s+/g, " ")
        .trim()
        .slice(0, 240),
    }));
}

export function demoClassify(input: AlertInput): AlertResult {
  const text = input.alert_text.toLowerCase();
  const low = /staging|sandbox|no customer impact|nightly|self-resolving/.test(
    text,
  );
  const page =
    input.current_severity === "P1" ||
    (!low && /5xx|outage|payment|customer impact/.test(text));
  const known = demoSearch(input.alert_text)[0] || null;
  return {
    recommended_severity: page ? "P2" : "P4",
    should_page: page,
    recommended_route: page
      ? "page_oncall"
      : known
        ? "dedupe_known_issue"
        : "ticket",
    dedupe_key: `${input.service || "unknown-service"}:demo:sample`,
    reason: page
      ? "Demo: customer-impacting keywords require on-call investigation."
      : "Demo: low-impact pattern can be tracked for review.",
    confidence: 0.8,
    known_issue: known,
    next_checks: [
      "Confirm customer impact and SLO burn.",
      "Check the runbook and incident owner.",
      "Review the recommendation before taking action.",
    ],
  };
}

export function demoReply(prompt: string): string {
  const sources = demoSearch(prompt).slice(0, 2);
  return `## First response plan\n\nThis is a **canned demo response**; no model, logs, or infrastructure were queried.\n\n1. Confirm the affected service, regions, and customer impact.\n2. Compare latency, error rate, and SLO burn with the last healthy baseline.\n3. Check the latest deployment and dependent services using read-only checks.\n4. Assign an incident owner and record an update before testing a mitigation.\n\n### Evidence to gather\n\n${sources.length ? sources.map((source) => `- ${source.citation} ${source.title}`).join("\n") : "- Search the runbook library for the affected service."}\n\n### Handoff\n\nRecord the current hypothesis, completed actions, next check, and rollback criteria in the incident board. Switch to **Live API** to ask your configured ADK agent.`;
}

export function seedIncidents(): Incident[] {
  const now = Date.now();
  const items: [
    string,
    string,
    string,
    Incident["severity"],
    Incident["status"],
    string,
    string,
  ][] = [
    [
      "INC-1042",
      "Checkout error rate above SLO",
      "checkout-api",
      "P2",
      "Investigating",
      "Mitra",
      "Elevated 5xx responses in the NA region following a checkout deployment. Confirm impact and compare dependency latency.",
    ],
    [
      "INC-1041",
      "Notification queue backlog",
      "notifications",
      "P3",
      "Mitigating",
      "Alex",
      "Queue depth increased during a batch import. Track drain rate and worker saturation before scaling.",
    ],
    [
      "INC-1040",
      "Nightly latency alert flapping",
      "checkout-api",
      "P4",
      "Resolved",
      "Sam",
      "Recurring nightly alert recovered with no customer impact. Review the known-issue runbook and alert threshold.",
    ],
  ];
  return items.map(
    ([id, title, service, severity, status, owner, summary], index) => {
      const at = new Date(now - (index + 1) * 32 * 60000).toISOString();
      return {
        id,
        title,
        service,
        severity,
        status,
        owner,
        summary,
        createdAt: at,
        tasks: [
          {
            id: `${id}-impact`,
            text: "Confirm customer impact and affected region",
            done: status !== "Investigating",
          },
          {
            id: `${id}-changes`,
            text: "Review recent changes and dependencies",
            done: status === "Resolved",
          },
          {
            id: `${id}-update`,
            text: "Publish the next incident update",
            done: status === "Resolved",
          },
        ],
        timeline: [
          {
            id: `${id}-opened`,
            at,
            text: "Demo incident opened for investigation.",
          },
        ],
      };
    },
  );
}
