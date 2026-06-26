import React from "react";
import { Form } from "antd";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CreateAssignment from "../../../../../pages/instructor/assignments/CreateAssignment";
import { getCourseInfo } from "../../../../../services/course";

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
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("shows the default AI feedback prompt immediately when AI feedback is enabled", async () => {
    const user = userEvent.setup();

    render(<CreateAssignmentHarness />);

    await waitFor(() => expect(getCourseInfo).toHaveBeenCalled());

    await user.click(screen.getAllByRole("switch")[1]);

    const promptInput = await screen.findByLabelText("AI Feedback Prompt");

    expect(promptInput.value).toEqual(
      expect.stringContaining("Always provide useful feedback")
    );
    expect(promptInput.value).toEqual(
      expect.stringContaining("Improvement Suggestions")
    );
  });
});
