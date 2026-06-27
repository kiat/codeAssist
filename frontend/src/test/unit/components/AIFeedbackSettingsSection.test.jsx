import React from "react";
import { Form } from "antd";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AIFeedbackSettingsSection from "../../../components/AIFeedbackSettingsSection";
import {
  DEFAULT_AI_ALLOWED_INPUTS,
  DEFAULT_AI_FEEDBACK_PROMPTS,
} from "../../../constants/aiFeedbackSettings";

function Harness() {
  const [form] = Form.useForm();

  return (
    <Form
      form={form}
      initialValues={{
        ai_feedback_prompts: DEFAULT_AI_FEEDBACK_PROMPTS,
        ai_allowed_inputs: DEFAULT_AI_ALLOWED_INPUTS,
        ai_feedback_max_requests: null,
        ai_feedback_wait_seconds: 0,
      }}
    >
      <AIFeedbackSettingsSection />
    </Form>
  );
}

describe("AIFeedbackSettingsSection", () => {
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

  it("renders editable prompts and input permission checkboxes", () => {
    render(<Harness />);

    expect(screen.getByDisplayValue("Check correctness")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Debug failed tests")).toBeInTheDocument();
    expect(screen.getByLabelText("Assignment description")).toBeChecked();
    expect(screen.getByLabelText("Student solution code")).toBeChecked();
    expect(screen.getByLabelText("Test cases")).not.toBeChecked();
  });

  it("renders usage limit inputs with default wait time", () => {
    render(<Harness />);

    expect(screen.getByText("AI Feedback Usage Limits")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Maximum feedback requests per student")
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Thinking time between requests")).toHaveValue("0");
  });

  it("adds a blank enabled prompt for the instructor to edit", async () => {
    const user = userEvent.setup();

    render(<Harness />);

    await user.click(screen.getByRole("button", { name: /add prompt/i }));

    await waitFor(() => {
      expect(screen.getByDisplayValue("New Prompt")).toBeInTheDocument();
    });
  });
});
