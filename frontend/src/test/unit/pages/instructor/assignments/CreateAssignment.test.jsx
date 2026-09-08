import React from "react";
import { Form } from "antd";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CreateAssignment from "../../../../../pages/instructor/assignments/CreateAssignment";
import { fetchAiModels, getCourseInfo } from "../../../../../services/course";
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

function CreateAssignmentHarness({ initialStep = 1 } = {}) {
  const [form] = Form.useForm();
  const [step, setStep] = React.useState(initialStep);

  return (
    <CreateAssignment
      currentStep={step}
      updateCurrentStep={setStep}
      toggleIsCreate={jest.fn()}
      nameValidationStatus=""
      form={form}
    />
  );
}

describe("CreateAssignment setup", () => {
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
    fetchAiModels.mockResolvedValue({ data: { models: ["gpt-4o-mini"] } });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("shows advanced AI prompt settings in a separate create section", async () => {
    const user = userEvent.setup();

    render(<CreateAssignmentHarness />);

    await waitFor(() => expect(getCourseInfo).toHaveBeenCalled());

    await user.click(screen.getByRole("switch", { name: /enable ai feedback/i }));

    expect(await screen.findByText("Current Course AI Default")).toBeInTheDocument();
    expect(
      screen.getByText("Prompts, input permissions, and usage limits")
    ).toBeInTheDocument();
    expect(await screen.findByText("Feedback Prompts")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Check correctness")).toBeInTheDocument();
    expect(screen.getByText("AI Input Permissions")).toBeInTheDocument();
    expect(screen.getByText("AI Feedback Usage Limits")).toBeInTheDocument();
  });

  it("includes edited AI usage limits in the create assignment payload", async () => {
    const user = userEvent.setup();

    render(<CreateAssignmentHarness />);

    await waitFor(() => expect(getCourseInfo).toHaveBeenCalled());

    await user.type(screen.getByLabelText(/assignment name/i), "Loops");
    await user.click(screen.getByRole("switch", { name: /enable ai feedback/i }));

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
          ai_feedback_enabled: true,
          ai_feedback_max_requests: 3,
          ai_feedback_wait_seconds: 60,
        })
      );
    });
  });

  it("includes assignment description in the create assignment payload", async () => {
    const user = userEvent.setup();

    render(<CreateAssignmentHarness />);

    await waitFor(() => expect(getCourseInfo).toHaveBeenCalled());

    await user.type(screen.getByLabelText(/assignment name/i), "Loops");
    await user.type(
      screen.getByLabelText(/assignment description/i),
      "Write a loop that prints every value exactly once."
    );

    await user.click(screen.getByRole("button", { name: /create assignment/i }));

    await waitFor(() => {
      expect(createAssignment).toHaveBeenCalledWith(
        expect.objectContaining({
          description: "Write a loop that prints every value exactly once.",
        })
      );
    });
  });

  it("creates AI-enabled assignments with the course default model source", async () => {
    const user = userEvent.setup();

    render(<CreateAssignmentHarness />);

    await waitFor(() => expect(getCourseInfo).toHaveBeenCalled());

    await user.type(screen.getByLabelText(/assignment name/i), "Loops");
    await user.click(screen.getByRole("switch", { name: /enable ai feedback/i }));

    await user.click(screen.getByRole("button", { name: /create assignment/i }));

    await waitFor(() => {
      expect(createAssignment).toHaveBeenCalledWith(
        expect.objectContaining({
          use_course_ai_default: true,
          ai_feedback_api_key: "",
        })
      );
    });
  });

  it("includes hold_grades in the create assignment payload when checked", async () => {
    const user = userEvent.setup();

    render(<CreateAssignmentHarness initialStep={0} />);
    await user.click(await screen.findByText(/programming assignment/i));

    await user.type(screen.getByLabelText(/assignment name/i), "Loops");
    await user.click(screen.getByLabelText(/hold grades until published/i));

    await user.click(screen.getByRole("button", { name: /create assignment/i }));

    await waitFor(() => {
      expect(createAssignment).toHaveBeenCalledWith(
        expect.objectContaining({ hold_grades: true })
      );
    });
  });

  it("defaults hold_grades to false when left unchecked", async () => {
    const user = userEvent.setup();

    render(<CreateAssignmentHarness initialStep={0} />);
    await user.click(await screen.findByText(/programming assignment/i));

    await user.type(screen.getByLabelText(/assignment name/i), "Loops");
    await user.click(screen.getByRole("button", { name: /create assignment/i }));

    await waitFor(() => {
      expect(createAssignment).toHaveBeenCalledWith(
        expect.objectContaining({ hold_grades: false })
      );
    });
  });

  it("shows late due date only when late submissions are enabled", async () => {
    const user = userEvent.setup();

    render(<CreateAssignmentHarness initialStep={0} />);

    await user.click(
      await screen.findByText(/programming assignment/i)
    );

    expect(
      screen.queryByLabelText(/late due date/i)
    ).not.toBeInTheDocument();

    await user.click(screen.getByLabelText(/allow late submissions/i));

    expect(
      await screen.findByLabelText(/late due date/i)
    ).toBeInTheDocument();
  });
});
