import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Modal } from "antd";
import CodeEditorPage from "../../../../pages/codeEditor";
import { GlobalContext } from "../../../../App";
import { getAssignment, getExtension } from "../../../../services/assignment";
import { getLatestDraft, saveCodeDraft, submitCode } from "../../../../services/submission";

const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  useParams: () => ({ assignmentId: "asgn-1" }),
  useNavigate: () => mockNavigate,
}));

jest.mock("../../../../services/assignment", () => ({
  getAssignment: jest.fn(),
  getExtension: jest.fn(),
}));

jest.mock("../../../../services/submission", () => ({
  aiChat: jest.fn(),
  saveCodeDraft: jest.fn(),
  getLatestDraft: jest.fn(),
  submitCode: jest.fn(),
  runCode: jest.fn(),
}));

// Stand-in editor that exposes the props the page passes down.
jest.mock("../../../../components/CodeEditor", () => {
  const React = require("react");
  return React.forwardRef((props, ref) => (
  <div ref={ref}>
    <span data-testid="file-name">{props.fileName}</span>
    <span data-testid="file-name-locked">{String(!!props.fileNameLocked)}</span>
    <button onClick={() => props.onFileNameChange("renamed.py")}>rename</button>
    <button onClick={props.onSubmit}>submit</button>
  </div>
  ));
});
jest.mock("../../../../components/AIChatPanel", () => require("react").forwardRef(() => null));
jest.mock("../../../../components/VersionHistoryModal", () => () => null);

const renderPage = () =>
  render(
    <GlobalContext.Provider value={{ userInfo: { id: "stu-1" }, courseInfo: {} }}>
      <CodeEditorPage />
    </GlobalContext.Provider>
  );

const assignment = (overrides = {}) => ({
  data: { name: "A2", due_date: null, late_submission: false, ...overrides },
});

beforeEach(() => {
  jest.clearAllMocks();
  getExtension.mockResolvedValue({ data: {} });
  saveCodeDraft.mockResolvedValue({ data: { id: "draft-2" } });
  submitCode.mockResolvedValue({ data: { submissionID: "sub-1" } });
  jest.spyOn(Modal, "confirm").mockImplementation(({ onOk }) => onOk());
});

afterEach(() => {
  Modal.confirm.mockRestore();
});

test("uses and locks the instructor's required file name", async () => {
  getAssignment.mockResolvedValue(assignment({ submission_files: ["spiral.py"] }));
  getLatestDraft.mockResolvedValue({ data: { id: "d1", content: "x = 1", file_name: "old.py" } });

  renderPage();

  await waitFor(() => expect(screen.getByTestId("file-name")).toHaveTextContent("spiral.py"));
  expect(screen.getByTestId("file-name-locked")).toHaveTextContent("true");

  await act(async () => {
    fireEvent.click(screen.getByText("submit"));
  });
  expect(submitCode).toHaveBeenCalledWith(expect.objectContaining({ file_name: "spiral.py" }));
});

test("restores the draft's file name so a resubmit keeps it", async () => {
  getAssignment.mockResolvedValue(assignment());
  getLatestDraft.mockResolvedValue({ data: { id: "d1", content: "x = 1", file_name: "spiral.py" } });

  renderPage();

  await waitFor(() => expect(screen.getByTestId("file-name")).toHaveTextContent("spiral.py"));
  expect(screen.getByTestId("file-name-locked")).toHaveTextContent("false");

  await act(async () => {
    fireEvent.click(screen.getByText("submit"));
  });
  await act(async () => {
    fireEvent.click(screen.getByText("submit"));
  });
  expect(submitCode).toHaveBeenCalledTimes(2);
  submitCode.mock.calls.forEach(([payload]) => expect(payload.file_name).toBe("spiral.py"));
});

test("falls back to the assignment-name default on a first visit", async () => {
  getAssignment.mockResolvedValue(assignment({ name: "Lab 3" }));
  getLatestDraft.mockResolvedValue({ data: null });

  renderPage();

  await waitFor(() => expect(screen.getByTestId("file-name")).toHaveTextContent("lab_3.py"));
});

test("renaming saves the new file name, not the old one", async () => {
  getAssignment.mockResolvedValue(assignment());
  getLatestDraft.mockResolvedValue({ data: { id: "d1", content: "x = 1", file_name: "old.py" } });

  renderPage();
  await waitFor(() => expect(screen.getByTestId("file-name")).toHaveTextContent("old.py"));

  await act(async () => {
    fireEvent.click(screen.getByText("rename"));
  });
  expect(saveCodeDraft).toHaveBeenCalledWith(expect.objectContaining({ file_name: "renamed.py" }));
});
