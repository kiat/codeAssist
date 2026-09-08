import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ReviewGrades from "../../../../pages/reviewGrades/index";
import { GlobalContext } from "../../../../App";
import { getGradeStatistics } from "../../../../services/submission";

const mockNavigate = jest.fn();
let mockParams = { assignmentId: "123" };
jest.mock("react-router-dom", () => {
  const original = jest.requireActual("react-router-dom");
  return {
    ...original,
    useNavigate: () => mockNavigate,
    useParams: () => mockParams,
    MemoryRouter: original.MemoryRouter,
  };
});

jest.mock("../../../../services/submission", () => ({
  getGradeStatistics: jest.fn(),
}));

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
  mockParams = { assignmentId: "123" };
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
        id: 10,
        student_id: 1,
        score: 88,
        active: true,
        submitted_at: 1658362327000,
      },
    ];

    const fakeStudents = [
      {
        id: 1,
        name: "Alice Example",
        email_address: "alice@example.com",
      },
      {
        id: 42,
        name: "Instructor",
        email_address: "instructor@example.com",
      },
    ];

    global.fetch = jest.fn()
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeSubmission),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeStudents),
    });
    getGradeStatistics.mockResolvedValue({ data: { max_points: 100 } });

    renderWithCtx();

    expect(
      screen.getByText("Review Grades for Midterm")
    ).toBeInTheDocument();

    await waitFor(() =>
      expect(screen.getByText("Alice Example")).toBeInTheDocument()
    );

    expect(screen.getByText("alice@example.com")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("88/100 (88%)")).toBeInTheDocument()
    );
  });

  it("only calls getGradeStatistics once per mount", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });
    getGradeStatistics.mockResolvedValue({ data: { max_points: 100 } });

    renderWithCtx();

    await waitFor(() => expect(getGradeStatistics).toHaveBeenCalled());
    expect(getGradeStatistics).toHaveBeenCalledTimes(1);
  });

  it("ignores a stale stats response after the assignment id changes", async () => {
    const fakeSubmission = [
      { id: 10, student_id: 1, score: 5, active: true, submitted_at: 1658362327000 },
    ];
    const fakeStudents = [
      { id: 1, name: "Alice Example", email_address: "alice@example.com" },
    ];
    global.fetch = jest.fn((url) =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve(
            url.includes("get_all_assignment_submissions") ? fakeSubmission : fakeStudents
          ),
      })
    );

    let resolveStale;
    getGradeStatistics
      .mockImplementationOnce(
        () => new Promise((resolve) => { resolveStale = resolve; })
      )
      .mockResolvedValueOnce({ data: { max_points: 10 } });

    const { rerender } = renderWithCtx();

    // Navigate to a different assignment before the first stats call resolves.
    mockParams = { assignmentId: "456" };
    rerender(
      <GlobalContext.Provider
        value={{
          assignmentInfo: { id: "456", name: "Midterm" },
          updateAssignmentInfo: jest.fn(),
          userInfo: { id: 42 },
          courseInfo: { id: 7 },
        }}
      >
        <MemoryRouter>
          <ReviewGrades />
        </MemoryRouter>
      </GlobalContext.Provider>
    );

    await waitFor(() =>
      expect(screen.getByText("5/10 (50%)")).toBeInTheDocument()
    );

    // The stale response now resolves with a different max_points; it must
    // not overwrite the current assignment's stats.
    resolveStale({ data: { max_points: 999 } });
    await waitFor(() => {});

    expect(screen.getByText("5/10 (50%)")).toBeInTheDocument();
    expect(screen.queryByText(/999/)).toBeNull();
  });

  it("falls back to a plain score when max_points is unavailable", async () => {
    const fakeSubmission = [
      {
        id: 10,
        student_id: 1,
        score: 88,
        active: true,
        submitted_at: 1658362327000,
      },
    ];

    const fakeStudents = [
      {
        id: 1,
        name: "Alice Example",
        email_address: "alice@example.com",
      },
    ];

    global.fetch = jest.fn()
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeSubmission),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeStudents),
    });
    getGradeStatistics.mockRejectedValue(new Error("network error"));

    renderWithCtx();

    await waitFor(() =>
      expect(screen.getByText("88")).toBeInTheDocument()
    );
  });
});
