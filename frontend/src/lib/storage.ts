import type { Conversation, Incident, Mode } from "./types";

export function readStored<T>(
  key: string,
  fallback: T,
  valid: (value: unknown) => value is T,
): T {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(key) || "null");
    return valid(value) ? value : fallback;
  } catch {
    return fallback;
  }
}

export function saveStored(key: string, value: unknown): boolean {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function validIncidents(value: unknown): value is Incident[] {
  return (
    Array.isArray(value) &&
    value.every(
      (item) =>
        isRecord(item) &&
        ["id", "title", "service", "owner", "summary", "createdAt"].every(
          (key) => typeof item[key] === "string",
        ) &&
        ["P1", "P2", "P3", "P4"].includes(String(item.severity)) &&
        ["Investigating", "Mitigating", "Resolved"].includes(
          String(item.status),
        ) &&
        Array.isArray(item.tasks) &&
        item.tasks.every(
          (task) =>
            isRecord(task) &&
            typeof task.id === "string" &&
            typeof task.text === "string" &&
            typeof task.done === "boolean",
        ) &&
        Array.isArray(item.timeline) &&
        item.timeline.every(
          (entry) =>
            isRecord(entry) &&
            typeof entry.id === "string" &&
            typeof entry.text === "string" &&
            typeof entry.at === "string",
        ),
    )
  );
}

export function validConversation(value: unknown): value is Conversation {
  return (
    isRecord(value) &&
    typeof value.sessionId === "string" &&
    Array.isArray(value.messages) &&
    value.messages.every(
      (message) =>
        isRecord(message) &&
        typeof message.id === "string" &&
        typeof message.text === "string" &&
        ["user", "assistant"].includes(String(message.role)),
    )
  );
}

export function workspaceKey(mode: Mode, kind: string): string {
  return `incidentiq:v1:${mode}:${kind}`;
}

export function getUserId(): string {
  const key = "incidentiq:v1:user";
  const existing = readStored(
    key,
    "",
    (value): value is string =>
      typeof value === "string" && /^web_[a-zA-Z0-9-]+$/.test(value),
  );
  if (existing) return existing;
  const id = `web_${crypto.randomUUID()}`;
  saveStored(key, id);
  return id;
}
