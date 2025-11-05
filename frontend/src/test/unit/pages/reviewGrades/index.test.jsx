import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ReviewGrades from "../../../../pages/reviewGrades/index";
import { GlobalContext } from "../../../../App";

const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => {
  const original = jest.requireActual("react-router-dom");
  return {
    ...original,
    useNavigate: () => mockNavigate,
    useParams: () => ({ assignmentId: "123" }),
    MemoryRouter: original.MemoryRouter,
  };
});

beforeAll(() => {
  window.matchMedia =
    window.matchMedia ||
    (() => ({
      matches: false,
      addListener: () => {},
      removeListener: () => {},
    }));
});

afterEach(() => {
  jest.clearAllMocks();
  delete global.fetch;
});

const renderWithCtx = (ctx = {}) => {
  const defaultCtx = {
    assignmentInfo: { id: "123", name: "Midterm" },
    updateAssignmentInfo: jest.fn(),
    userInfo: { id: 42 },
    courseInfo: { id: 7 },
  };
  return render(
    <GlobalContext.Provider value={{ ...defaultCtx, ...ctx }}>
      <MemoryRouter>
        <ReviewGrades />
      </MemoryRouter>
    </GlobalContext.Provider>
  );
};

describe("<ReviewGrades />", () => {
  it('redirects to "/" if userInfo.id is missing', () => {
    renderWithCtx({ userInfo: {} });
    expect(mockNavigate).toHaveBeenCalledWith("/");
  });

  it("renders header and fetches + displays a submission row", async () => {
    const fakeSubmission = [
      {
        id: 1,
        student_name: "Alice Example",
        email_address: "alice@example.com",
        score: 88,
        graded: 1,
        viewed: 0,
        submitted_at: 1658362327000,
        time: 1658362327000,
      },
    ];
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(fakeSubmission),
    });

    renderWithCtx();

    expect(
      screen.getByText("Review Grades for Midterm")
    ).toBeInTheDocument();

    await waitFor(() =>
      expect(screen.getByText("Alice Example")).toBeInTheDocument()
    );

    expect(screen.getByText("alice@example.com")).toBeInTheDocument();
    expect(screen.getByText("88")).toBeInTheDocument();
  });
});
