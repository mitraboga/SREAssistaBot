import { useEffect, useRef, useState } from "react";
import {
  ArrowUp,
  Bot,
  CheckCheck,
  Clock3,
  Plus,
  RefreshCw,
  Square,
  Sparkles,
} from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { Badge, ErrorNotice, Markdown, SourceLink } from "../components/ui";
import { ApiError, loadSessionMessages, sendLiveMessage } from "../lib/api";
import { demoReply } from "../lib/demo";
import {
  getUserId,
  readStored,
  saveStored,
  validConversation,
  workspaceKey,
} from "../lib/storage";
import { useWorkspace } from "../lib/workspace";
import type { Conversation } from "../lib/types";

const prompts = [
  [
    "First response plan",
    "Create a first 15-minute response plan for checkout 5xx errors with customer impact in NA.",
  ],
  [
    "Reliability review",
    "Review an API backed by Postgres and Redis: suggest SLIs, SLOs, and alerts.",
  ],
  [
    "Incident handoff",
    "Help me structure an incident handoff with current impact, evidence, owner, and next actions.",
  ],
];

function freshConversation(): Conversation {
  return { sessionId: `web_${crypto.randomUUID()}`, messages: [] };
}

export function Assistant() {
  const { mode, incidents } = useWorkspace();
  const [params] = useSearchParams();
  const incident = incidents.find((item) => item.id === params.get("incident"));
  const [conversation, setConversation] = useState<Conversation>(() =>
    readStored(
      workspaceKey(mode, "chat"),
      freshConversation(),
      validConversation,
    ),
  );
  const [userId] = useState(getUserId);
  const [draft, setDraft] = useState(
    incident ? `Create a first-response plan for ${incident.title}.` : "",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [storageError, setStorageError] = useState(false);
  const [latency, setLatency] = useState<number | null>(null);
  const controller = useRef<AbortController | null>(null);
  const lastPrompt = useRef("");
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    setStorageError(!saveStored(workspaceKey(mode, "chat"), conversation));
  }, [conversation, mode]);
  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [conversation.messages, busy]);
  useEffect(
    () => () => {
      controller.current?.abort();
      controller.current = null;
    },
    [],
  );

  async function send(prompt: string, append = true) {
    if (controller.current || !prompt.trim()) return;
    const current = new AbortController();
    controller.current = current;
    setBusy(true);
    setError("");
    setLatency(null);
    lastPrompt.current = prompt;
    if (append)
      setConversation((value) => ({
        ...value,
        messages: [
          ...value.messages,
          { id: crypto.randomUUID(), role: "user", text: prompt },
        ],
      }));
    setDraft("");
    const start = performance.now();
    try {
      const answer =
        mode === "demo"
          ? demoReply(prompt)
          : await sendLiveMessage(
              userId,
              conversation.sessionId,
              prompt,
              current.signal,
            );
      if (controller.current !== current || current.signal.aborted) return;
      setConversation((value) => ({
        ...value,
        messages: [
          ...value.messages,
          { id: crypto.randomUUID(), role: "assistant", text: answer },
        ],
      }));
      setLatency(performance.now() - start);
    } catch (failure) {
      if (controller.current !== current) return;
      setError(
        current.signal.aborted
          ? "Request cancelled. The backend may still complete; sync history before retrying."
          : failure instanceof Error
            ? failure.message
            : "The request failed. Please retry.",
      );
    } finally {
      if (controller.current === current) {
        controller.current = null;
        setBusy(false);
      }
    }
  }
  async function syncHistory() {
    if (controller.current || mode === "demo") return;
    const current = new AbortController();
    controller.current = current;
    setBusy(true);
    setError("");
    try {
      const messages = await loadSessionMessages(
        userId,
        conversation.sessionId,
        current.signal,
      );
      if (controller.current === current)
        setConversation((value) => ({ ...value, messages }));
    } catch (failure) {
      if (controller.current === current)
        setError(
          failure instanceof ApiError && failure.status === 404
            ? "This session has not been created on the backend yet. Send a message to start it."
            : failure instanceof Error
              ? failure.message
              : "History sync failed.",
        );
    } finally {
      if (controller.current === current) {
        controller.current = null;
        setBusy(false);
      }
    }
  }
  function newChat() {
    controller.current?.abort();
    controller.current = null;
    setBusy(false);
    setError("");
    setLatency(null);
    lastPrompt.current = "";
    setConversation(freshConversation());
  }
  function submit() {
    const text = draft.trim();
    if (!text) return;
    const context = incident
      ? `Incident ${incident.id}\nService: ${incident.service}\nSeverity: ${incident.severity}\nOwner: ${incident.owner || "Unassigned"}\nContext: ${incident.summary}\n\n`
      : "";
    void send(context + text);
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">FROM SIGNAL TO NEXT STEP</p>
          <h1>SRE assistant</h1>
          <p>
            Investigate with context. Turn a messy report into a clear response.
          </p>
        </div>
        <button className="secondary" onClick={newChat}>
          <Plus size={16} />
          New conversation
        </button>
      </div>
      <div className="assistant-grid">
        <section
          className="panel chat-panel"
          aria-label="SRE assistant conversation"
        >
          <div className="panel-heading">
            <h2>
              <span className="agent-avatar">
                <Bot size={17} />
              </span>
              IncidentIQ assistant
            </h2>
            <Badge tone="green">
              {mode === "demo" ? "Canned demo" : "ADK agent"}
            </Badge>
          </div>
          {incident && (
            <div className="context-strip">
              <CheckCheck size={15} />
              <span>
                Context attached: <strong>{incident.id}</strong> ·{" "}
                {incident.service}
              </span>
            </div>
          )}
          <div
            className="chat-log"
            role="log"
            aria-live="polite"
            aria-label="Conversation messages"
          >
            {!conversation.messages.length && (
              <div className="chat-welcome">
                <span className="welcome-icon">
                  <Sparkles size={26} />
                </span>
                <p className="eyebrow">YOUR INVESTIGATION PARTNER</p>
                <h2>What are we looking into?</h2>
                <p>
                  Describe the symptoms, affected service, and what changed.
                  <br />
                  We’ll make the next step clear.
                </p>
                <div className="prompt-grid">
                  {prompts.map(([title, text]) => (
                    <button
                      key={title}
                      className="prompt-card"
                      onClick={() => setDraft(text)}
                    >
                      <strong>{title}</strong>
                      <span>{text}</span>
                      <ArrowUp size={15} />
                    </button>
                  ))}
                </div>
              </div>
            )}
            {conversation.messages.map((message) => (
              <article key={message.id} className={`message ${message.role}`}>
                <span
                  className={
                    message.role === "user" ? "avatar" : "agent-avatar"
                  }
                >
                  {message.role === "user" ? "YOU" : <Bot size={18} />}
                </span>
                <div>
                  <div className="message-label">
                    {message.role === "user" ? "You" : "IncidentIQ"}
                    {message.role === "assistant" && mode === "demo" && (
                      <Badge tone="neutral">Demo</Badge>
                    )}
                  </div>
                  <Markdown text={message.text} />
                  {message.role === "assistant" && (
                    <div className="citation-links">
                      {[
                        ...new Set(
                          message.text.match(/\b(?:RB|PI)-\d{3}\b/g) || [],
                        ),
                      ].map((id) => (
                        <SourceLink id={id} key={id} />
                      ))}
                    </div>
                  )}
                </div>
              </article>
            ))}
            {busy && (
              <div className="thinking" role="status">
                <span className="spinner" />
                {mode === "live"
                  ? "Waiting for the agent…"
                  : "Preparing demo guidance…"}
              </div>
            )}
            <div ref={end} />
          </div>
          <div className="composer-wrap">
            {error && (
              <>
                <ErrorNotice message={error} />
                <div className="error-actions">
                  {lastPrompt.current && (
                    <button
                      disabled={busy}
                      onClick={() => {
                        void send(lastPrompt.current, false);
                      }}
                    >
                      Retry request
                    </button>
                  )}
                  {mode === "live" && (
                    <button
                      disabled={busy}
                      onClick={() => {
                        void syncHistory();
                      }}
                    >
                      Sync history
                    </button>
                  )}
                </div>
              </>
            )}
            {storageError && (
              <ErrorNotice message="Conversation could not be saved in browser storage." />
            )}
            <form
              className="composer"
              onSubmit={(event) => {
                event.preventDefault();
                submit();
              }}
            >
              <textarea
                aria-label="Message the SRE assistant"
                placeholder="Describe an incident or ask a reliability question…"
                maxLength={10000}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" &&
                    !event.shiftKey &&
                    !event.nativeEvent.isComposing
                  ) {
                    event.preventDefault();
                    if (!busy) submit();
                  }
                }}
              />
              <div className="composer-bottom">
                <span>Enter to send · Shift + Enter for a new line</span>
                {busy ? (
                  <button
                    className="send-button"
                    type="button"
                    onClick={() => controller.current?.abort()}
                    aria-label="Cancel request"
                  >
                    <Square size={16} />
                  </button>
                ) : (
                  <button
                    className="send-button"
                    type="submit"
                    disabled={!draft.trim()}
                    aria-label="Send message"
                  >
                    <ArrowUp size={19} />
                  </button>
                )}
              </div>
            </form>
            <p className="composer-note">
              {mode === "demo"
                ? "Demo responses are canned. No infrastructure was queried."
                : "AI guidance needs review. No remediation runs from this interface."}
            </p>
          </div>
        </section>
        <aside className="assistant-aside">
          <section className="panel guide-panel">
            <p className="eyebrow">BETTER CONTEXT, BETTER ANSWERS</p>
            <h3>A useful incident report</h3>
            <ol>
              <li>
                <strong>What’s affected?</strong>
                <span>Service, region, and customer impact.</span>
              </li>
              <li>
                <strong>What’s the signal?</strong>
                <span>Errors, latency, and SLO burn.</span>
              </li>
              <li>
                <strong>What changed?</strong>
                <span>Deployments, config, or dependencies.</span>
              </li>
              <li>
                <strong>What’s been tried?</strong>
                <span>Checks completed and their results.</span>
              </li>
            </ol>
          </section>
          <section className="panel guide-panel">
            <h3>Conversation details</h3>
            <dl>
              <dt>Environment</dt>
              <dd>{mode === "demo" ? "Offline demo" : "Configured backend"}</dd>
              <dt>Messages</dt>
              <dd>{conversation.messages.length}</dd>
              <dt>
                <Clock3 size={13} />
                Last response
              </dt>
              <dd>
                {latency === null ? "—" : `${(latency / 1000).toFixed(2)}s`}
              </dd>
            </dl>
            <p className="muted small">
              Response time is measured in this browser. It is not token-level
              TTFT.
            </p>
            {mode === "live" && (
              <button
                className="secondary full-width"
                disabled={busy}
                onClick={() => {
                  void syncHistory();
                }}
              >
                <RefreshCw size={14} />
                Sync ADK history
              </button>
            )}
          </section>
        </aside>
      </div>
    </>
  );
}
