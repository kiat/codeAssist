import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AssignmentSettings from "../../../../pages/assignmentSettings";
import { GlobalContext } from "../../../../App";
import {
  getAssignment,
  updateAssignment,
} from "../../../../services/assignment";
import { getCourseInfo, fetchAiModels } from "../../../../services/course";

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
  useParams: () => ({ assignmentId: "assignment-1" }),
}));

jest.mock("../../../../services/assignment", () => ({
  deleteAssignment: jest.fn(),
  deleteSubmissions: jest.fn(),
  getAssignment: jest.fn(),
  updateAssignment: jest.fn(),
}));

jest.mock("../../../../services/course", () => ({
  getCourseInfo: jest.fn(),
  fetchAiModels: jest.fn(),
}));

function renderAssignmentSettings() {
  return render(
    <GlobalContext.Provider
      value={{
        updateAssignmentInfo: jest.fn(),
      }}
    >
      <AssignmentSettings />
    </GlobalContext.Provider>
  );
}

describe("AssignmentSettings late submissions", () => {
  beforeEach(() => {
    getAssignment.mockResolvedValue({
      data: {
        id: "assignment-1",
        name: "Homework 1",
        course_id: "course-1",
        published: false,
        published_date: "2026-07-01T12:00:00Z",
        due_date: "2026-07-08T12:00:00Z",
        autograder_points: 100,
        late_submission: false,
        late_due_date: "2026-07-09T12:00:00Z",
        allow_file_upload: true,
        enable_code_editor: true,
        ai_feedback_enabled: false,
        use_course_ai_default: true,
      },
    });
    getCourseInfo.mockResolvedValue({ data: [{}] });
    fetchAiModels.mockResolvedValue({ data: { models: [] } });
    updateAssignment.mockResolvedValue({ data: { message: "updated" } });
  });

  afterEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
  });

  it("hides stale late due date and submits null when late submissions are disabled", async () => {
    const user = userEvent.setup();

    renderAssignmentSettings();

    await screen.findByDisplayValue("Homework 1");

    expect(
      screen.queryByLabelText(/late due date/i)
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      expect(updateAssignment).toHaveBeenCalledWith(
        expect.objectContaining({
          assignment_id: "assignment-1",
          late_submission: false,
          late_due_date: null,
        })
      );
    });
  });
});
