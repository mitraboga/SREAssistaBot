import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { expect, it } from "vitest";
import { WorkspaceProvider } from "../lib/workspace";
import { IncidentBoard } from "./IncidentBoard";

it("filters the queue and updates the selected incident actions", async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter>
      <WorkspaceProvider>
        <IncidentBoard />
      </WorkspaceProvider>
    </MemoryRouter>,
  );
  await user.type(
    screen.getByRole("textbox", { name: "Search incidents" }),
    "notifications",
  );
  expect(screen.getAllByRole("row")).toHaveLength(2);
  await user.clear(screen.getByRole("textbox", { name: "Search incidents" }));
  await user.click(
    screen.getByRole("checkbox", {
      name: "Confirm customer impact and affected region",
    }),
  );
  expect(
    screen.getByRole("checkbox", {
      name: "Confirm customer impact and affected region",
    }),
  ).toBeChecked();
  expect(
    screen.getByText("Completed: Confirm customer impact and affected region"),
  ).toBeInTheDocument();
});
