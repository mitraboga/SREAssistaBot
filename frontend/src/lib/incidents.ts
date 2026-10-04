import type { Incident, IncidentStatus, TimelineEntry } from "./types";

export type IncidentAction =
  | { type: "create"; incident: Incident }
  | { type: "status"; id: string; status: IncidentStatus; at: string }
  | { type: "owner"; id: string; owner: string; at: string }
  | { type: "task"; id: string; taskId: string; at: string }
  | { type: "addTask"; id: string; taskId: string; text: string; at: string }
  | { type: "note"; id: string; text: string; at: string };

export function incidentReducer(
  state: Incident[],
  action: IncidentAction,
): Incident[] {
  if (action.type === "create") return [action.incident, ...state];
  return state.map((incident) => {
    if (incident.id !== action.id) return incident;
    let next = { ...incident };
    let text: string;
    switch (action.type) {
      case "status":
        if (incident.status === action.status) return incident;
        next.status = action.status;
        text = `Status changed to ${action.status.toLowerCase()}.`;
        break;
      case "owner":
        if (incident.owner === action.owner) return incident;
        next.owner = action.owner;
        text = `Incident owner: ${action.owner || "Unassigned"}.`;
        break;
      case "task": {
        const task = incident.tasks.find((item) => item.id === action.taskId);
        if (!task) return incident;
        next.tasks = incident.tasks.map((item) =>
          item.id === task.id ? { ...item, done: !item.done } : item,
        );
        text = `${task.done ? "Reopened" : "Completed"}: ${task.text}`;
        break;
      }
      case "addTask":
        next.tasks = [
          ...incident.tasks,
          { id: action.taskId, text: action.text, done: false },
        ];
        text = `Action added: ${action.text}`;
        break;
      case "note":
        text = action.text;
        break;
    }
    const entry: TimelineEntry = {
      id: crypto.randomUUID(),
      text,
      at: action.at,
    };
    next = { ...next, timeline: [entry, ...incident.timeline] };
    return next;
  });
}

export function handoffMarkdown(incident: Incident): string {
  return [
    `# ${incident.id} — ${incident.title}`,
    "",
    `- Service: ${incident.service}`,
    `- Severity: ${incident.severity}`,
    `- Status: ${incident.status}`,
    `- Owner: ${incident.owner || "Unassigned"}`,
    `- Opened: ${incident.createdAt}`,
    "",
    "## Summary",
    "",
    incident.summary,
    "",
    "## Actions",
    "",
    ...incident.tasks.map(
      (task) => `- [${task.done ? "x" : " "}] ${task.text}`,
    ),
    "",
    "## Timeline",
    "",
    ...incident.timeline.map((entry) => `- ${entry.at}: ${entry.text}`),
    "",
  ].join("\n");
}
