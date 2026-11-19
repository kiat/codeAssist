import React from "react";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AssignmentResult from "../../../../pages/result";
import { GlobalContext } from "../../../../App";
import { getAssignment, getExtension } from "../../../../services/assignment";
import {
  getSubmissionStatus,
  rerunSubmissionAutograder,
} from "../../../../services/submission";

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
  getSubmissionStatus: jest.fn(),
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

  const failedSubmission = {
    id: "submission-1",
    assignment_id: "assignment-1",
    student_id: "student-1",
    name: "Ada",
    score: null,
    status: "failed",
    student_code_file: "print('hello')",
    file_name: "solution.py",
    results: null,
  };

  it("shows the results after rerunning a failed submission", async () => {
    const user = userEvent.setup();
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(failedSubmission),
    });
    rerunSubmissionAutograder.mockResolvedValue({
      data: {
        message: "Autograder rerun completed",
        submission: { ...failedSubmission, status: "graded", score: 9, results: { tests: [] } },
      },
    });

    renderAssignmentResult();
    expect(await screen.findByText("Grading failed")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /rerun autograder/i }));

    expect(await screen.findByTestId("result-score")).toHaveTextContent("9");
    expect(screen.queryByText("Grading failed")).not.toBeInTheDocument();
  });

  it("reloads the submission when the rerun request fails", async () => {
    const user = userEvent.setup();
    // Before the rerun the row is failed. A timed-out rerun returns an error
    // but still records a graded row, which the page should reload.
    global.fetch = jest.fn(async () => ({
      ok: true,
      json: () =>
        Promise.resolve(
          rerunSubmissionAutograder.mock.calls.length === 0
            ? failedSubmission
            : { ...failedSubmission, status: "graded", score: 7, results: { tests: [] } }
        ),
    }));
    rerunSubmissionAutograder.mockRejectedValue(new Error("504"));

    renderAssignmentResult();
    expect(await screen.findByText("Grading failed")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /rerun autograder/i }));

    expect(await screen.findByTestId("result-score")).toHaveTextContent("7");
    expect(screen.queryByText("Grading failed")).not.toBeInTheDocument();
  });
});

describe("AssignmentResult grading status", () => {
  const baseSubmission = {
    id: "submission-1",
    assignment_id: "assignment-1",
    student_id: "student-1",
    name: "Ada",
    student_code_file: "print('hello')",
    file_name: "solution.py",
    results: { tests: [] },
  };

  const detailsResponse = (overrides) => ({
    ok: true,
    json: () => Promise.resolve({ ...baseSubmission, ...overrides }),
  });
  const failedResponse = () => ({
    ok: false,
    json: () => Promise.resolve({ message: "Server error" }),
  });

  beforeEach(() => {
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
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
  });

  it("shows a queued message instead of results while pending", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValue(detailsResponse({ status: "pending", score: null }));
    getSubmissionStatus.mockResolvedValue({ data: { status: "pending" } });

    renderAssignmentResult();

    expect(await screen.findByText("Queued for grading")).toBeInTheDocument();
    expect(screen.queryByTestId("result-score")).not.toBeInTheDocument();
  });

  it("polls until graded, then shows results", async () => {
    jest.useFakeTimers();
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(detailsResponse({ status: "pending", score: null }))
      .mockResolvedValue(detailsResponse({ status: "graded", score: 9 }));
    getSubmissionStatus
      .mockResolvedValueOnce({ data: { status: "running" } })
      .mockResolvedValueOnce({ data: { status: "graded" } });

    renderAssignmentResult();
    expect(await screen.findByText("Queued for grading")).toBeInTheDocument();

    await act(async () => {
      jest.advanceTimersByTime(2000);
    });
    expect(await screen.findByText("Grading")).toBeInTheDocument();

    await act(async () => {
      jest.advanceTimersByTime(2000);
    });
    expect(await screen.findByTestId("result-score")).toHaveTextContent("9");
    expect(screen.queryByText("Grading")).not.toBeInTheDocument();
    expect(getSubmissionStatus).toHaveBeenCalledWith({ submission_id: "submission-1" });
  });

  it("keeps polling when fetching the graded details fails once", async () => {
    jest.useFakeTimers();
    // Page-load fetches see "running". After polling starts, the first details
    // request fails and the next one succeeds.
    let pollDetailsCalls = 0;
    global.fetch = jest.fn(async () => {
      if (getSubmissionStatus.mock.calls.length === 0) {
        return detailsResponse({ status: "running", score: null });
      }
      pollDetailsCalls += 1;
      return pollDetailsCalls === 1
        ? failedResponse()
        : detailsResponse({ status: "graded", score: 9 });
    });
    getSubmissionStatus.mockResolvedValue({ data: { status: "graded" } });

    renderAssignmentResult();
    expect(await screen.findByText("Grading")).toBeInTheDocument();

    await act(async () => {
      jest.advanceTimersByTime(2000);
    });
    expect(screen.queryByTestId("result-score")).not.toBeInTheDocument();
    expect(screen.getByText("Grading")).toBeInTheDocument();

    await act(async () => {
      jest.advanceTimersByTime(2000);
    });
    expect(await screen.findByTestId("result-score")).toHaveTextContent("9");
  });

  it("disables Rerun Autograder while the submission is being graded", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValue(detailsResponse({ status: "pending", score: null }));
    getSubmissionStatus.mockResolvedValue({ data: { status: "pending" } });

    renderAssignmentResult();
    await screen.findByText("Queued for grading");

    expect(screen.getByRole("button", { name: /Rerun Autograder/ })).toBeDisabled();
  });

  it("shows a failure message and does not poll when grading failed", async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValue(detailsResponse({ status: "failed", score: null }));

    renderAssignmentResult();

    expect(await screen.findByText("Grading failed")).toBeInTheDocument();
    expect(screen.queryByTestId("result-score")).not.toBeInTheDocument();
    expect(getSubmissionStatus).not.toHaveBeenCalled();
  });
});
