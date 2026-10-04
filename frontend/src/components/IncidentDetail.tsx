import { useState } from "react";
import {
  ArrowDownToLine,
  ArrowUpRight,
  Check,
  Clock3,
  ListChecks,
  Plus,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Badge, formatTime } from "./ui";
import { handoffMarkdown } from "../lib/incidents";
import { useWorkspace } from "../lib/workspace";
import type { Incident, IncidentStatus } from "../lib/types";
const statuses: IncidentStatus[] = ["Investigating", "Mitigating", "Resolved"];

export function IncidentDetail({ incident }: { incident: Incident }) {
  const { dispatch } = useWorkspace();
  const [owner, setOwner] = useState(incident.owner);
  const [task, setTask] = useState("");
  const [note, setNote] = useState("");
  const at = () => new Date().toISOString();
  function exportHandoff() {
    const url = URL.createObjectURL(
      new Blob([handoffMarkdown(incident)], { type: "text/markdown" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${incident.id}-handoff.md`;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <section className="panel detail-panel" aria-label="Incident details">
      <div className="panel-heading">
        <span className="mono muted">{incident.id}</span>
        <button
          className="icon-button"
          onClick={exportHandoff}
          aria-label="Export incident handoff"
          title="Export handoff"
        >
          <ArrowDownToLine size={17} />
        </button>
      </div>
      <div className="detail-title">
        <Badge tone={incident.severity.toLowerCase()}>
          {incident.severity}
        </Badge>
        <h2>{incident.title}</h2>
        <p>{incident.summary}</p>
      </div>
      <div className="detail-controls">
        <label>
          Status
          <select
            aria-label="Status"
            value={incident.status}
            onChange={(event) =>
              dispatch({
                type: "status",
                id: incident.id,
                status: event.target.value as IncidentStatus,
                at: at(),
              })
            }
          >
            {statuses.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            dispatch({
              type: "owner",
              id: incident.id,
              owner: owner.trim(),
              at: at(),
            });
          }}
        >
          <label>
            Incident owner
            <div className="inline-field">
              <input
                aria-label="Incident owner"
                maxLength={80}
                value={owner}
                onChange={(event) => setOwner(event.target.value)}
                placeholder="Unassigned"
              />
              <button type="submit" aria-label="Save owner">
                <Check size={16} />
              </button>
            </div>
          </label>
        </form>
      </div>
      <div className="detail-section">
        <h3>
          <ListChecks size={15} />
          Response actions
          <span>
            {incident.tasks.filter((item) => item.done).length}/
            {incident.tasks.length}
          </span>
        </h3>
        <div className="task-list">
          {incident.tasks.map((item) => (
            <label key={item.id} className={item.done ? "done" : ""}>
              <input
                type="checkbox"
                checked={item.done}
                onChange={() =>
                  dispatch({
                    type: "task",
                    id: incident.id,
                    taskId: item.id,
                    at: at(),
                  })
                }
              />
              <span>{item.text}</span>
            </label>
          ))}
        </div>
        <form
          className="inline-field"
          onSubmit={(event) => {
            event.preventDefault();
            if (!task.trim()) return;
            dispatch({
              type: "addTask",
              id: incident.id,
              taskId: crypto.randomUUID(),
              text: task.trim(),
              at: at(),
            });
            setTask("");
          }}
        >
          <input
            aria-label="New response action"
            placeholder="Add an action…"
            maxLength={300}
            value={task}
            onChange={(event) => setTask(event.target.value)}
          />
          <button
            type="submit"
            aria-label="Add response action"
            disabled={!task.trim()}
          >
            <Plus size={17} />
          </button>
        </form>
      </div>
      <div className="detail-section">
        <h3>
          <Clock3 size={15} />
          Response timeline
        </h3>
        <form
          className="note-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (!note.trim()) return;
            dispatch({
              type: "note",
              id: incident.id,
              text: note.trim(),
              at: at(),
            });
            setNote("");
          }}
        >
          <textarea
            aria-label="Timeline update"
            maxLength={2000}
            placeholder="Record evidence or the next update…"
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
          <button type="submit" className="secondary" disabled={!note.trim()}>
            Add update
          </button>
        </form>
        <ol className="timeline">
          {incident.timeline.slice(0, 12).map((entry) => (
            <li key={entry.id}>
              <span className="timeline-dot" />
              <div>
                <p>{entry.text}</p>
                <time dateTime={entry.at}>{formatTime(entry.at)}</time>
              </div>
            </li>
          ))}
        </ol>
      </div>
      <div className="detail-bottom">
        <Link to={`/assistant?incident=${encodeURIComponent(incident.id)}`}>
          Investigate with assistant <ArrowUpRight size={14} />
        </Link>
      </div>
    </section>
  );
}
