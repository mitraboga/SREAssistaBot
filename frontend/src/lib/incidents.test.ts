import { describe, expect, it } from "vitest";
import { seedIncidents } from "./demo";
import { handoffMarkdown, incidentReducer } from "./incidents";

describe("incident coordination", () => {
  it("updates a task immutably and adds a timestamped audit entry", () => {
    const state = seedIncidents();
    const next = incidentReducer(state, {
      type: "task",
      id: state[0].id,
      taskId: state[0].tasks[0].id,
      at: "2026-10-04T10:00:00Z",
    });
    expect(state[0].tasks[0].done).toBe(false);
    expect(next[0].tasks[0].done).toBe(true);
    expect(next[0].timeline[0].at).toBe("2026-10-04T10:00:00Z");
    expect(next[1]).toBe(state[1]);
  });
  it("ignores missing tasks and unchanged status without adding history noise", () => {
    const state = seedIncidents();
    expect(
      incidentReducer(state, {
        type: "task",
        id: state[0].id,
        taskId: "missing",
        at: "",
      })[0],
    ).toBe(state[0]);
    expect(
      incidentReducer(state, {
        type: "status",
        id: state[0].id,
        status: state[0].status,
        at: "",
      })[0],
    ).toBe(state[0]);
  });
  it("exports the complete owner, actions, and timeline in a handoff", () => {
    const incident = seedIncidents()[0];
    const output = handoffMarkdown(incident);
    expect(output).toContain(`Owner: ${incident.owner}`);
    expect(output).toContain("- [ ] Confirm customer impact");
    expect(output).toContain(incident.timeline[0].at);
  });
});
