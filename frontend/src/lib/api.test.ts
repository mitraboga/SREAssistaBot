import { describe, expect, it, vi } from "vitest";
import { ApiError, extractAssistantText, sendLiveMessage } from "./api";

describe("ADK integration", () => {
  it("selects final answer text and excludes user, reasoning, and partial output", () => {
    expect(
      extractAssistantText([
        { author: "user", content: { parts: [{ text: "question" }] } },
        {
          author: "sre_agent",
          partial: true,
          content: { parts: [{ text: "partial" }] },
        },
        {
          author: "sre_agent",
          content: { parts: [{ text: "thinking", thought: true }] },
        },
        {
          author: "sre_agent",
          content: { parts: [{ text: "Check SLO burn." }] },
        },
        { author: "tool", content: { parts: [{ functionResponse: {} }] } },
      ]),
    ).toBe("Check SLO burn.");
  });
  it("fails explicitly for malformed or text-free responses", () => {
    expect(() => extractAssistantText({})).toThrow("Unexpected ADK");
    expect(() => extractAssistantText([])).toThrow("no answer text");
  });
  it("creates only a missing session and sends the expected run payload", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response("{}", { status: 404 }))
      .mockResolvedValueOnce(new Response("{}"))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify([
            { author: "sre_agent", content: { parts: [{ text: "answer" }] } },
          ]),
        ),
      );
    expect(
      await sendLiveMessage(
        "web_user",
        "web_session",
        "question",
        new AbortController().signal,
      ),
    ).toBe("answer");
    expect(
      fetchMock.mock.calls.map((call) => call[1]?.method || "GET"),
    ).toEqual(["GET", "POST", "POST"]);
    const body = JSON.parse(String(fetchMock.mock.calls[2][1]?.body));
    expect(body).toEqual({
      app_name: "sre_agent",
      user_id: "web_user",
      session_id: "web_session",
      new_message: { role: "user", parts: [{ text: "question" }] },
    });
  });
  it("preserves existing sessions and never masks server failures as missing sessions", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response("{}", { status: 503 }));
    await expect(
      sendLiveMessage(
        "web_user",
        "web_session",
        "question",
        new AbortController().signal,
      ),
    ).rejects.toBeInstanceOf(ApiError);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
  it("returns a useful error when the backend is unreachable", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(
      new TypeError("network error"),
    );
    await expect(
      sendLiveMessage(
        "web_user",
        "web_session",
        "question",
        new AbortController().signal,
      ),
    ).rejects.toThrow("Cannot reach the API");
  });
});
