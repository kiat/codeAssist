import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TestResultsDisplay from "../../../../pages/result/TestResultsDisplay";
import { GlobalContext } from "../../../../App";

jest.mock("../../../../pages/result/StudentInfoPanel", () => () => (
  <div data-testid="student-info-panel" />
));

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
  useParams: () => ({ submissionId: "submission-1" }),
}));

describe("TestResultsDisplay AI feedback", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      json: () => Promise.resolve({ score: 10 }),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("shows AI insights and success state when there are no line annotations", async () => {
    const user = userEvent.setup();
    const data = {
      score: 10,
      results: { tests: [] },
      student_code_file: "def add(a, b):\n    return a + b\n",
      file_name: "student.py",
      ai_feedback: JSON.stringify({
        insights: [
          "Overall Summary: The submission passes the available tests.",
          "Improvement Suggestion: Consider edge cases around invalid input.",
        ],
        annotations: [],
      }),
    };

    render(
      <GlobalContext.Provider value={{ userInfo: { id: "user-1" }, courseInfo: {} }}>
        <TestResultsDisplay
          viewMode="Code"
          assignmentName="Calculator"
          studentName="Ada Lovelace"
          score={10}
          totalPoints={10}
          data={data}
          aiFeedbackEnabled
        />
      </GlobalContext.Provider>
    );

    await user.click(await screen.findByText("student.py"));

    expect(await screen.findByText("AI Feedback Summary")).toBeInTheDocument();
    expect(
      screen.getByText("Overall Summary: The submission passes the available tests.")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Improvement Suggestion: Consider edge cases around invalid input.")
    ).toBeInTheDocument();
    expect(screen.getByText("AI Feedback Ready")).toBeInTheDocument();
    expect(screen.getByText("No line-by-line annotations")).toBeInTheDocument();

    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
  });
});
