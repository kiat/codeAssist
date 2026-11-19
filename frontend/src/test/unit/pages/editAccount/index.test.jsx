import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { message } from "antd";
import EditAccount from "../../../../pages/editAccount";

const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

const ACCOUNT = {
  id: "u1",
  name: "Pat",
  sis_user_id: "pat1",
  email_address: "pat@example.com",
  has_password: true,
};

function mockFetch({ account = ACCOUNT, update = { status: 200, body: { message: "Account updated successfully" } } } = {}) {
  global.fetch = jest.fn((url) => {
    if (String(url).includes("/get_user_by_id")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(account) });
    }
    return Promise.resolve({
      ok: update.status < 400,
      status: update.status,
      json: () => Promise.resolve(update.body),
    });
  });
}

const updateCalls = () => global.fetch.mock.calls.filter(([url]) => String(url).includes("/update_account"));
const sentBody = () => JSON.parse(updateCalls()[0][1].body);

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.setItem("userInfo", JSON.stringify({ id: "u1" }));
  jest.spyOn(message, "success").mockImplementation(() => {});
  jest.spyOn(message, "error").mockImplementation(() => {});
  jest.spyOn(message, "info").mockImplementation(() => {});
});

afterEach(() => {
  jest.restoreAllMocks();
  localStorage.clear();
});

async function renderLoaded(options) {
  mockFetch(options);
  render(<EditAccount />);
  await waitFor(() => expect(screen.getByLabelText("EID")).toHaveValue("pat1"));
}

test("a new password needs the current one, and a matching confirmation", async () => {
  await renderLoaded();

  await userEvent.type(screen.getByLabelText("New password"), "brand-new-pass");
  await userEvent.type(screen.getByLabelText("Confirm new password"), "something-else");
  await userEvent.click(screen.getByRole("button", { name: /update account/i }));

  expect(await screen.findByText("The new passwords don't match")).toBeInTheDocument();
  expect(await screen.findByText("Enter your current password")).toBeInTheDocument();
  expect(updateCalls()).toHaveLength(0);
});

test("a short new password is rejected before sending", async () => {
  await renderLoaded();

  await userEvent.type(screen.getByLabelText("New password"), "short");
  await userEvent.click(screen.getByRole("button", { name: /update account/i }));

  expect(await screen.findByText("Use at least 8 characters")).toBeInTheDocument();
  expect(updateCalls()).toHaveLength(0);
});

test("sends the current password with the new one, with the session cookie, then goes home", async () => {
  await renderLoaded();

  await userEvent.type(screen.getByLabelText("New password"), "brand-new-pass");
  await userEvent.type(screen.getByLabelText("Confirm new password"), "brand-new-pass");
  await userEvent.type(screen.getByLabelText("Current password"), "old-password");
  await userEvent.click(screen.getByRole("button", { name: /update account/i }));

  await waitFor(() => expect(updateCalls()).toHaveLength(1));
  expect(updateCalls()[0][1].credentials).toBe("include");
  expect(sentBody()).toEqual({ id: "u1", password: "brand-new-pass", current_password: "old-password" });
  await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith("/dashboard"));
  expect(message.success).toHaveBeenCalledWith("Password changed");
});

test("a name change sends no password fields", async () => {
  await renderLoaded();

  await userEvent.type(screen.getByLabelText("Name"), "Patricia");
  await userEvent.click(screen.getByRole("button", { name: /update account/i }));

  await waitFor(() => expect(updateCalls()).toHaveLength(1));
  expect(sentBody()).toEqual({ id: "u1", name: "Patricia" });
});

test("a wrong current password shows the server's message and stays on the page", async () => {
  await renderLoaded({ update: { status: 403, body: { message: "Current password is incorrect" } } });

  await userEvent.type(screen.getByLabelText("New password"), "brand-new-pass");
  await userEvent.type(screen.getByLabelText("Confirm new password"), "brand-new-pass");
  await userEvent.type(screen.getByLabelText("Current password"), "wrong");
  await userEvent.click(screen.getByRole("button", { name: /update account/i }));

  await waitFor(() => expect(message.error).toHaveBeenCalledWith("Current password is incorrect"));
  expect(mockNavigate).not.toHaveBeenCalled();
});

test("a Google-only account sees a note instead of the password fields", async () => {
  await renderLoaded({ account: { ...ACCOUNT, has_password: false } });

  expect(screen.getByText("You sign in with Google, so there is no password to change.")).toBeInTheDocument();
  expect(screen.queryByLabelText("New password")).toBeNull();
  expect(screen.queryByLabelText("Current password")).toBeNull();
});
