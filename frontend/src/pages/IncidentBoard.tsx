import { useState } from "react";
import type { FormEvent } from "react";
import {
  ArrowUpRight,
  Check,
  Clock3,
  ListChecks,
  Plus,
  Search,
  ShieldAlert,
  Users,
  X,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Badge } from "../components/ui";
import { IncidentDetail } from "../components/IncidentDetail";
import { useWorkspace } from "../lib/workspace";
import type { Incident, IncidentStatus, Severity } from "../lib/types";

const statuses: IncidentStatus[] = ["Investigating", "Mitigating", "Resolved"];

export function IncidentBoard() {
  const { mode, incidents, dispatch } = useWorkspace();
  const [selectedId, setSelectedId] = useState(incidents[0]?.id || "");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("All incidents");
  const [creating, setCreating] = useState(false);
  const filtered = incidents.filter(
    (item) =>
      (status === "All incidents" || item.status === status) &&
      `${item.title} ${item.service} ${item.id} ${item.owner}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const selected = incidents.find((item) => item.id === selectedId);
  const open = incidents.filter((item) => item.status !== "Resolved");
  const tasks = incidents.flatMap((item) => item.tasks);
  const complete = tasks.filter((item) => item.done).length;
  function create(incident: Incident) {
    dispatch({ type: "create", incident });
    setSelectedId(incident.id);
    setCreating(false);
    setStatus("All incidents");
    setQuery("");
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">RELIABILITY, IN FOCUS</p>
          <h1>
            Incident board
            <span className="heading-dot" />
          </h1>
          <p>
            One place to coordinate the response and keep the next step clear.
          </p>
        </div>
        <button className="primary" onClick={() => setCreating(!creating)}>
          {creating ? <X size={16} /> : <Plus size={16} />}
          {creating ? "Close form" : "New incident"}
        </button>
      </div>
      <div className="stats-grid">
        <Stat
          icon={<ShieldAlert size={19} />}
          label="Open incidents"
          value={open.length}
          detail="Investigating or mitigating"
          tone="orange"
        />
        <Stat
          icon={<Clock3 size={19} />}
          label="Needs attention"
          value={
            open.filter(
              (item) => item.severity === "P1" || item.severity === "P2",
            ).length
          }
          detail="Open P1 & P2 incidents"
          tone="red"
        />
        <Stat
          icon={<ListChecks size={19} />}
          label="Actions complete"
          value={`${complete}/${tasks.length}`}
          detail="Across this workspace"
          tone="green"
        />
        <Stat
          icon={<Users size={19} />}
          label="Awaiting an owner"
          value={open.filter((item) => !item.owner).length}
          detail="Open incidents without an owner"
          tone="blue"
        />
      </div>
      {creating && <CreateIncident onCreate={create} />}
      <div className="board-grid">
        <section className="panel incident-list">
          <div className="panel-heading">
            <h2>
              Response queue <span className="count">{incidents.length}</span>
            </h2>
            <Badge tone={mode === "demo" ? "neutral" : "green"}>
              {mode === "demo" ? "Sample data" : "Browser local"}
            </Badge>
          </div>
          <div className="list-tools">
            <label className="search-field">
              <Search size={16} />
              <input
                aria-label="Search incidents"
                placeholder="Search incidents, services, owners…"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <select
              aria-label="Filter by status"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
            >
              <option>All incidents</option>
              {statuses.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Incident</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Owner</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => (
                  <tr
                    key={item.id}
                    className={selectedId === item.id ? "selected" : ""}
                  >
                    <td>
                      <button
                        className="incident-select"
                        onClick={() => setSelectedId(item.id)}
                        aria-pressed={selectedId === item.id}
                      >
                        <span className="mono muted">{item.id}</span>
                        <strong>{item.title}</strong>
                        <small>{item.service}</small>
                      </button>
                    </td>
                    <td>
                      <Badge tone={item.severity.toLowerCase()}>
                        {item.severity}
                      </Badge>
                    </td>
                    <td>
                      <span
                        className={`status-dot ${item.status.toLowerCase()}`}
                      />
                      {item.status}
                    </td>
                    <td>
                      <span className="owner-cell">
                        {item.owner && (
                          <span className="tiny-avatar">
                            {item.owner.slice(0, 1)}
                          </span>
                        )}
                        {item.owner || "Unassigned"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!filtered.length && (
            <div className="empty-state">
              <Search size={24} />
              <h3>
                {incidents.length
                  ? "No matching incidents"
                  : "Your queue is clear"}
              </h3>
              <p>
                {incidents.length
                  ? "Try another search or status filter."
                  : "Create an incident to track a response."}
              </p>
            </div>
          )}
          <div className="panel-footer">
            <span>
              {filtered.length} of {incidents.length} incidents
            </span>
            <span>Saved in this browser</span>
          </div>
        </section>
        {selected ? (
          <IncidentDetail key={selected.id} incident={selected} />
        ) : (
          <section className="panel empty-state">
            <ShieldAlert size={30} />
            <h3>Start with an incident</h3>
            <p>Track the owner, actions, and handoff in one place.</p>
          </section>
        )}
      </div>
      <section className="workflow-card">
        <div>
          <span className="icon-tile">
            <Check size={20} />
          </span>
          <div>
            <h3>A clear handoff is a better response.</h3>
            <p>
              Keep hypotheses, evidence, and next actions together. Use the
              assistant to structure your investigation.
            </p>
          </div>
        </div>
        <Link to="/assistant">
          Open SRE assistant <ArrowUpRight size={16} />
        </Link>
      </section>
    </>
  );
}

function Stat({
  icon,
  label,
  value,
  detail,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  detail: string;
  tone: string;
}) {
  return (
    <section className="stat-card">
      <div>
        <span>{label}</span>
        <span className={`stat-icon ${tone}`}>{icon}</span>
      </div>
      <strong>{value}</strong>
      <p>{detail}</p>
    </section>
  );
}

function CreateIncident({
  onCreate,
}: {
  onCreate: (incident: Incident) => void;
}) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const title = String(form.get("title") || "").trim();
    const service = String(form.get("service") || "").trim();
    const summary = String(form.get("summary") || "").trim();
    if (!title || !service || !summary) return;
    const at = new Date().toISOString();
    onCreate({
      id: `INC-${crypto.randomUUID().slice(0, 8).toUpperCase()}`,
      title,
      service,
      severity: String(form.get("severity")) as Severity,
      status: "Investigating",
      owner: String(form.get("owner") || "").trim(),
      summary,
      createdAt: at,
      tasks: [
        {
          id: crypto.randomUUID(),
          text: "Confirm customer impact and affected scope",
          done: false,
        },
      ],
      timeline: [
        {
          id: crypto.randomUUID(),
          at,
          text: "Incident opened for investigation.",
        },
      ],
    });
  }
  return (
    <section className="panel create-panel">
      <h2>New incident</h2>
      <form onSubmit={submit} className="create-form">
        <label>
          Incident title
          <input
            autoFocus
            name="title"
            required
            maxLength={160}
            placeholder="What needs investigation?"
            pattern=".*\S.*"
          />
        </label>
        <label>
          Service
          <input
            name="service"
            required
            maxLength={100}
            placeholder="e.g. checkout-api"
            pattern=".*\S.*"
          />
        </label>
        <label>
          Severity
          <select name="severity" defaultValue="P3">
            {["P1", "P2", "P3", "P4"].map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label>
          Owner
          <input name="owner" maxLength={80} placeholder="Optional" />
        </label>
        <label className="full-width">
          Impact & context
          <textarea
            name="summary"
            required
            maxLength={5000}
            placeholder="Symptoms, affected users, region, and recent changes…"
          />
        </label>
        <div className="full-width">
          <button className="primary" type="submit">
            <Plus size={15} />
            Create incident
          </button>
        </div>
      </form>
    </section>
  );
}
