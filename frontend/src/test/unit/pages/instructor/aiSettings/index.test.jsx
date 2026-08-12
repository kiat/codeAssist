import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AISettings from "../../../../../pages/instructor/aiSettings";
import { GlobalContext } from "../../../../../App";
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

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useParams: () => ({ courseId: "course-1" }),
  useNavigate: () => mockNavigate,
}));

function renderAISettings(courseRole = "instructor") {
  return render(
    <GlobalContext.Provider value={{ courseRole }}>
      <AISettings />
    </GlobalContext.Provider>
  );
}

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
    renderAISettings();

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

    renderAISettings();

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

  it("does not redirect an instructor away from AI settings", async () => {
    renderAISettings("instructor");

    await screen.findByText("gpt-4o-mini");

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it("redirects a TA away from AI settings", async () => {
    renderAISettings("ta");

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/instructorDashboard/course-1");
    });
  });

  it("redirects a student away from AI settings", async () => {
    renderAISettings("student");

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/instructorDashboard/course-1");
    });
  });
});
