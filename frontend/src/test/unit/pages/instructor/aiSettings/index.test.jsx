import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AISettings from "../../../../../pages/instructor/aiSettings";
import {
  fetchAiModels,
  getCourseInfo,
  testAiModel,
  updateAiSettings,
} from "../../../../../services/course";

jest.mock("../../../../../services/course", () => ({
  getCourseInfo: jest.fn(),
  updateAiSettings: jest.fn(),
  fetchAiModels: jest.fn(),
  testAiModel: jest.fn(),
}));

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useParams: () => ({ courseId: "course-1" }),
}));

describe("AISettings model testing", () => {
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
    fetchAiModels.mockResolvedValue({
      data: { models: ["gpt-4o-mini", "gpt-4o"] },
    });
    testAiModel.mockResolvedValue({ data: { message: "ok" } });
    updateAiSettings.mockResolvedValue({ data: { message: "saved" } });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("places test selected model after the default model selector", async () => {
    render(<AISettings />);

    const refreshButton = await screen.findByRole("button", {
      name: /refresh models/i,
    });
    const testButton = screen.getByRole("button", {
      name: /test selected model/i,
    });

    expect(
      refreshButton.compareDocumentPosition(testButton) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
  });

  it("tests the selected default model", async () => {
    const user = userEvent.setup();

    render(<AISettings />);

    await screen.findByText("gpt-4o-mini");
    await user.click(
      screen.getByRole("button", { name: /test selected model/i })
    );

    await waitFor(() => {
      expect(testAiModel).toHaveBeenCalledWith({
        course_id: "course-1",
        provider: "openai",
        model: "gpt-4o-mini",
        api_key: undefined,
      });
    });
  });

  it("shows Vertex AI as server-managed configuration", async () => {
    const user = userEvent.setup();
    getCourseInfo.mockResolvedValueOnce({
      data: [
        {
          default_ai_provider: "gemini_vertex",
          default_ai_model: "gemini-2.5-flash",
          default_feedback_style: "balanced",
          default_ai_temperature: 0.5,
          has_gemini_vertex_config: true,
        },
      ],
    });
    fetchAiModels.mockResolvedValueOnce({
      data: { models: ["gemini-2.5-flash", "gemini-2.5-pro"] },
    });

    render(<AISettings />);

    expect(
      await screen.findByText("Vertex AI Server Configuration")
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Gemini over Vertex AI uses the Google Cloud project and credentials configured for the CodeAssist deployment."
      )
    ).toBeInTheDocument();
    expect(
      screen.queryByPlaceholderText(/paste a new api key/i)
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /refresh models/i }));

    await waitFor(() => {
      expect(fetchAiModels).toHaveBeenCalledWith({
        course_id: "course-1",
        provider: "gemini_vertex",
        api_key: undefined,
      });
    });
  });
});
