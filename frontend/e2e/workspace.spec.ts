import { expect, test } from "@playwright/test";

test("coordinates an incident, persists it, and exports a handoff", async ({
  page,
}) => {
  await page.goto("/incidents");
  await page.getByRole("button", { name: "New incident" }).click();
  await page
    .getByLabel("Incident title", { exact: true })
    .fill("Auth token refresh failures");
  await page.getByLabel("Service", { exact: true }).fill("auth-api");
  await page
    .getByLabel("Impact & context")
    .fill("Customer login failures after a config change.");
  await page
    .getByRole("button", { name: "Create incident", exact: true })
    .click();
  const details = page.getByRole("region", { name: "Incident details" });
  await details.getByLabel("Incident owner", { exact: true }).fill("Mitra");
  await page.getByRole("button", { name: "Save owner" }).click();
  await details
    .getByLabel("Status", { exact: true })
    .selectOption("Mitigating");
  await page
    .getByRole("checkbox", {
      name: "Confirm customer impact and affected scope",
    })
    .check();
  await page
    .getByLabel("Timeline update")
    .fill("Config rollback validated in staging.");
  await page.getByRole("button", { name: "Add update" }).click();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export incident handoff" }).click();
  expect((await downloadPromise).suggestedFilename()).toMatch(/handoff\.md$/);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Auth token refresh failures" }),
  ).toBeVisible();
  await expect(page.getByLabel("Timeline update")).toBeVisible();
  await expect(
    page.getByText("Config rollback validated in staging."),
  ).toBeVisible();
  await expect(
    page.getByRole("checkbox", {
      name: "Confirm customer impact and affected scope",
    }),
  ).toBeChecked();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("uses demo chat, follows citations, and reviews alert routing", async ({
  page,
}) => {
  await page.goto("/assistant");
  await page
    .getByRole("textbox", { name: "Message the SRE assistant" })
    .fill("checkout 5xx payment failures in NA");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(
    page.getByText("canned demo response", { exact: true }),
  ).toBeVisible();
  await page.locator(".citation-links a").first().click();
  await expect(page.locator(".source-body")).toBeVisible();
  await page.getByRole("link", { name: "Alert triage", exact: true }).click();
  await page.getByRole("button", { name: "Customer-impacting errors" }).click();
  await page.getByRole("button", { name: "Review routing" }).click();
  await expect(
    page.getByRole("heading", { name: "Page on-call", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Recurring nightly noise" }).click();
  await page.getByRole("button", { name: "Review routing" }).click();
  await expect(
    page.getByRole("heading", { name: "Review known issue" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("integrates the live ADK contract and shows retryable errors without demo fallback", async ({
  page,
}) => {
  let runCount = 0;
  let sessionCreated = false;
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === "/api/health")
      return route.fulfill({ json: { status: "healthy" } });
    if (path.includes("/sessions/")) {
      if (request.method() === "POST") {
        sessionCreated = true;
        return route.fulfill({ json: { id: "test-session" } });
      }
      return route.fulfill({
        status: sessionCreated ? 200 : 404,
        json: { events: [] },
      });
    }
    if (path === "/api/run") {
      expect(request.postDataJSON().new_message.parts[0].text).toBe(
        "Inspect checkout latency",
      );
      runCount += 1;
      return runCount === 1
        ? route.fulfill({
            status: 503,
            json: { detail: "Provider unavailable" },
          })
        : route.fulfill({
            json: [
              {
                author: "sre_agent",
                content: {
                  role: "model",
                  parts: [
                    { text: "Check the checkout SLO and dependency latency." },
                  ],
                },
              },
            ],
          });
    }
    return route.fulfill({ status: 404, json: {} });
  });
  await page.goto("/assistant");
  await page.getByLabel("Environment", { exact: true }).selectOption("live");
  await page
    .getByRole("textbox", { name: "Message the SRE assistant" })
    .fill("Inspect checkout latency");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(page.getByRole("alert")).toContainText("503");
  await page.getByRole("button", { name: "Retry request" }).click();
  await expect(
    page.getByText("Check the checkout SLO and dependency latency.", {
      exact: true,
    }),
  ).toBeVisible();
  expect(sessionCreated).toBe(true);
  await expect(
    page.getByText("canned demo response", { exact: true }),
  ).toHaveCount(0);
});
