import { describe, expect, it, vi } from "vitest";
import {
  readStored,
  saveStored,
  validIncidents,
  workspaceKey,
} from "./storage";

describe("browser persistence", () => {
  it("recovers from corrupted JSON and invalid data", () => {
    localStorage.setItem("broken", "{");
    expect(readStored("broken", [], validIncidents)).toEqual([]);
    localStorage.setItem("broken", '[{"title":"partial"}]');
    expect(readStored("broken", [], validIncidents)).toEqual([]);
  });
  it("isolates demo and live records", () => {
    expect(workspaceKey("demo", "incidents")).not.toBe(
      workspaceKey("live", "incidents"),
    );
  });
  it("reports storage failures instead of throwing", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("Quota", "QuotaExceededError");
    });
    expect(saveStored("key", {})).toBe(false);
  });
});
