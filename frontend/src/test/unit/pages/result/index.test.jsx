import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AssignmentResult from "../../../../pages/result";
import { GlobalContext } from "../../../../App";
import { getAssignment, getExtension } from "../../../../services/assignment";
import { rerunSubmissionAutograder } from "../../../../services/submission";

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
  useParams: () => ({ submissionId: "submission-1" }),
}));

jest.mock("../../../../services/assignment", () => ({
  getAssignment: jest.fn(),
  getExtension: jest.fn(),
}));

jest.mock("../../../../services/submission", () => ({
  rerunSubmissionAutograder: jest.fn(),
}));

jest.mock("../../../../pages/result/TestResultsDisplay", () => ({ data }) => (
  <div data-testid="result-score">{data?.score}</div>
));

jest.mock("../../../../components/UploadModal", () => () => (
  <div data-testid="upload-modal" />
));

jest.mock("../../../../pages/result/submissionHistoryModal", () => () => (
  <div data-testid="history-modal" />
));

jest.mock("../../../../pages/result/FormattingModal", () => () => (
  <div data-testid="formatting-modal" />
));

function renderAssignmentResult() {
  return render(
    <GlobalContext.Provider
      value={{
        userInfo: { id: "student-1", name: "Ada", isStudent: true },
        assignmentInfo: {},
        updateAssignmentInfo: jest.fn(),
      }}
    >
      <AssignmentResult />
    </GlobalContext.Provider>
  );
}

describe("AssignmentResult rerun autograder", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      json: () =>
        Promise.resolve({
          id: "submission-1",
          assignment_id: "assignment-1",
          student_id: "student-1",
          name: "Ada",
          score: 5,
          student_code_file: "print('hello')",
          file_name: "solution.py",
          results: { tests: [] },
        }),
    });

    getAssignment.mockResolvedValue({
      data: {
        id: "assignment-1",
        name: "Homework 1",
        autograder_points: 10,
        due_date: "2099-01-01T00:00:00Z",
        late_due_date: "2099-01-02T00:00:00Z",
        late_submission: true,
        ai_feedback_enabled: false,
        allow_file_upload: true,
        enable_code_editor: true,
      },
    });
    getExtension.mockResolvedValue({ data: {} });
    rerunSubmissionAutograder.mockResolvedValue({
      data: {
        message: "Autograder rerun completed",
        submission: {
          id: "submission-1",
          assignment_id: "assignment-1",
          student_id: "student-1",
          score: 9,
          student_code_file: "print('hello')",
          file_name: "solution.py",
          results: { tests: [] },
        },
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("reruns the autograder for the current submission and updates results", async () => {
    const user = userEvent.setup();

    renderAssignmentResult();

    expect(await screen.findByTestId("result-score")).toHaveTextContent("5");

    await user.click(
      screen.getByRole("button", { name: /rerun autograder/i })
    );

    await waitFor(() => {
      expect(rerunSubmissionAutograder).toHaveBeenCalledWith({
        submission_id: "submission-1",
      });
    });
    expect(await screen.findByTestId("result-score")).toHaveTextContent("9");
  });
});
