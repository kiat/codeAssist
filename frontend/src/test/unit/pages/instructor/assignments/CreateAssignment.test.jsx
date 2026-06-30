import React from "react";
import { Form } from "antd";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CreateAssignment from "../../../../../pages/instructor/assignments/CreateAssignment";
import { getCourseInfo } from "../../../../../services/course";
import { createAssignment } from "../../../../../services/assignment";

jest.mock("../../../../../services/course", () => ({
  getCourseInfo: jest.fn(),
  fetchAiModels: jest.fn(),
}));

jest.mock("../../../../../services/assignment", () => ({
  createAssignment: jest.fn(),
  updateAssignment: jest.fn(),
}));

jest.mock("../../../../../services/submission", () => ({
  uploadAssignmentAutograder: jest.fn(),
}));

jest.mock("../../../../../pages/configureAutograder/AutograderSection", () => () => (
  <div data-testid="autograder-section" />
));

jest.mock("../../../../../pages/configureAutograder/TestAutograder", () => () => (
  <div data-testid="test-autograder" />
));

jest.mock("../../../../../pages/result/TestResultsDisplay", () => () => (
  <div data-testid="test-results-display" />
));

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useParams: () => ({ courseId: "course-1" }),
}));

function CreateAssignmentHarness() {
  const [form] = Form.useForm();

  return (
    <CreateAssignment
      currentStep={1}
      updateCurrentStep={jest.fn()}
      toggleIsCreate={jest.fn()}
      nameValidationStatus=""
      form={form}
    />
  );
}

describe("CreateAssignment AI prompt defaults", () => {
  beforeAll(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: jest.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });
  });

  beforeEach(() => {
    getCourseInfo.mockResolvedValue({
      data: [
        {
          default_ai_provider: "openai",
          default_ai_model: "gpt-4o-mini",
          default_feedback_style: "balanced",
          default_ai_temperature: 0.5,
          has_openai_api_key: true,
        },
      ],
    });
    createAssignment.mockResolvedValue({ id: "assignment-1" });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("shows the default AI feedback prompts immediately when AI feedback is enabled", async () => {
    const user = userEvent.setup();

    render(<CreateAssignmentHarness />);

    await waitFor(() => expect(getCourseInfo).toHaveBeenCalled());

    await user.click(screen.getAllByRole("switch")[1]);

    expect(await screen.findByText("Feedback Prompts")).toBeInTheDocument();

    expect(screen.getByDisplayValue("Check correctness")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Debug failed tests")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Review edge cases")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Explain runtime errors")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Review code style")).toBeInTheDocument();
    expect(
      screen.getByDisplayValue("Suggest algorithmic improvements")
    ).toBeInTheDocument();

    expect(screen.getByText("AI Input Permissions")).toBeInTheDocument();
    expect(screen.getByText("AI Feedback Usage Limits")).toBeInTheDocument();
    expect(screen.getByLabelText("Assignment description")).toBeChecked();
    expect(screen.getByLabelText("Student solution code")).toBeChecked();
  });

  it("includes AI usage limits in the create assignment payload", async () => {
    const user = userEvent.setup();

    render(<CreateAssignmentHarness />);

    await waitFor(() => expect(getCourseInfo).toHaveBeenCalled());

    await user.type(screen.getByLabelText(/assignment name/i), "Loops");
    await user.click(screen.getAllByRole("switch")[1]);

    await user.type(
      await screen.findByLabelText("Maximum feedback requests per student"),
      "3"
    );

    const waitSecondsInput = screen.getByLabelText(
      "Minimum seconds between requests (0 = no wait)"
    );
    await user.clear(waitSecondsInput);
    await user.type(waitSecondsInput, "60");

    await user.click(screen.getByRole("button", { name: /create assignment/i }));

    await waitFor(() => {
      expect(createAssignment).toHaveBeenCalledWith(
        expect.objectContaining({
          ai_feedback_max_requests: 3,
          ai_feedback_wait_seconds: 60,
        })
      );
    });
  });
});
