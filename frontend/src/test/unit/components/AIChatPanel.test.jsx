import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import AIChatPanel from "../../../components/AIChatPanel";

// Mock the services
jest.mock("../../../services/assignment", () => ({
  getAssignmentPrompts: jest.fn(),
}));

jest.mock("../../../services/submission", () => ({
  aiFeedbackStatus: jest.fn(),
}));

import { getAssignmentPrompts } from "../../../services/assignment";
import { aiFeedbackStatus } from "../../../services/submission";

// Mock scrollIntoView for jsdom
beforeAll(() => {
  Element.prototype.scrollIntoView = jest.fn();
});

const mockPrompts = [
  { id: "check_correctness", title: "Check correctness", prompt: "Check correctness prompt", enabled: true },
  { id: "debug_failed_tests", title: "Debug failed tests", prompt: "Debug prompt", enabled: true },
  { id: "review_edge_cases", title: "Review edge cases", prompt: "Edge cases prompt", enabled: false },
];

const mockStatus = {
  remaining: 5,
  wait_seconds: 0,
  max_requests: 10,
  total_requests: 5,
};

beforeEach(() => {
  jest.clearAllMocks();
  getAssignmentPrompts.mockResolvedValue({
    data: { ai_feedback_prompts: mockPrompts },
  });
  aiFeedbackStatus.mockResolvedValue({
    data: mockStatus,
  });
});

describe("AIChatPanel", () => {
  const defaultProps = {
    onSendMessage: jest.fn().mockResolvedValue({ reply: "AI response", feedback_status: { remaining: 4, wait_seconds: 0 } }),
    code: "print('hello')",
    disabled: false,
    assignmentId: "asgn-1",
    studentId: "stu-1",
  };

  it("renders the AI Assistant header", async () => {
    render(<AIChatPanel {...defaultProps} />);
    expect(screen.getByText("AI Assistant")).toBeInTheDocument();
  });

  it("fetches and displays only enabled instructor prompts", async () => {
    render(<AIChatPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Check correctness")).toBeInTheDocument();
    });

    expect(screen.getByText("Debug failed tests")).toBeInTheDocument();
    expect(screen.queryByText("Review edge cases")).not.toBeInTheDocument();
  });

  it("shows remaining request count when max_requests is set", async () => {
    render(<AIChatPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("5 left")).toBeInTheDocument();
    });
  });

  it("shows limit reached when remaining is 0", async () => {
    aiFeedbackStatus.mockResolvedValue({
      data: { remaining: 0, wait_seconds: 0, max_requests: 10, total_requests: 10 },
    });

    render(<AIChatPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Limit reached")).toBeInTheDocument();
    });
  });

  it("disables prompt buttons when limit is reached", async () => {
    aiFeedbackStatus.mockResolvedValue({
      data: { remaining: 0, wait_seconds: 0, max_requests: 10, total_requests: 10 },
    });

    render(<AIChatPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Limit reached")).toBeInTheDocument();
    });

    const buttons = screen.getAllByRole("button");
    buttons.forEach((btn) => {
      expect(btn).toBeDisabled();
    });
  });

  it("shows countdown when wait_seconds > 0", async () => {
    aiFeedbackStatus.mockResolvedValue({
      data: { remaining: 3, wait_seconds: 30, max_requests: 10, total_requests: 7 },
    });

    render(<AIChatPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/Please wait/)).toBeInTheDocument();
    });
  });

  it("sends prompt_id when a prompt is clicked", async () => {
    const onSendMessage = jest.fn().mockResolvedValue({
      reply: "AI response",
      feedback_status: { remaining: 4, wait_seconds: 0 },
    });

    render(<AIChatPanel {...defaultProps} onSendMessage={onSendMessage} />);

    await waitFor(() => {
      expect(screen.getByText("Check correctness")).toBeInTheDocument();
    });

    // Click the first prompt button
    const buttons = screen.getAllByRole("button");
    const checkBtn = buttons.find((btn) => btn.textContent.includes("Check correctness"));
    if (checkBtn) {
      checkBtn.click();
    }

    await waitFor(() => {
      expect(onSendMessage).toHaveBeenCalledWith(
        "Check correctness",
        "print('hello')",
        "check_correctness"
      );
    });
  });

  it("shows welcome message initially", async () => {
    render(<AIChatPanel {...defaultProps} />);
    expect(screen.getByText(/Hi! I'm your AI coding assistant/)).toBeInTheDocument();
  });

  it("shows no prompts available when prompts list is empty", async () => {
    getAssignmentPrompts.mockResolvedValue({
      data: { ai_feedback_prompts: [] },
    });

    render(<AIChatPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("No prompts available")).toBeInTheDocument();
    });
  });
});
