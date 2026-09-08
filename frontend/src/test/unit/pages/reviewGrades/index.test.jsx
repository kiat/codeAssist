import React from "react";
import { render, screen, waitFor, fireEvent, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ReviewGrades from "../../../../pages/reviewGrades/index";
import { GlobalContext } from "../../../../App";
import { publishGrades } from "../../../../services/submission";

jest.mock("../../../../services/submission", () => ({
  ...jest.requireActual("../../../../services/submission"),
  publishGrades: jest.fn(),
}));

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
      json: () => Promise.resolve({ hold_grades: false, grades_published: false }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeSubmission),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(fakeStudents),
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

  it("does not render the Publish Grades button when hold_grades is false", async () => {
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ hold_grades: false, grades_published: false }),
      })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    renderWithCtx();

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(3));
    expect(screen.queryByText("Publish Grades")).toBeNull();
  });

  it("renders Publish Grades and opens the confirmation modal when hold_grades is true", async () => {
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ hold_grades: true, grades_published: false }),
      })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    renderWithCtx();

    await waitFor(() =>
      expect(screen.getByText("Publish Grades")).toBeInTheDocument()
    );

    fireEvent.click(screen.getByText("Publish Grades"));

    expect(
      await screen.findByRole("dialog", { name: "Publish Grades" })
    ).toBeInTheDocument();
  });

  it("toggles the button to Unpublish Grades after a successful publish", async () => {
    publishGrades.mockResolvedValue({
      data: { assignment_id: "123", grades_published: true, grades_published_at: "2026-08-25T00:00:00Z" },
    });

    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ hold_grades: true, grades_published: false }),
      })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve([]) });

    renderWithCtx();

    await waitFor(() =>
      expect(screen.getByText("Publish Grades")).toBeInTheDocument()
    );
    fireEvent.click(screen.getByText("Publish Grades"));

    const dialog = await screen.findByRole("dialog", { name: "Publish Grades" });
    fireEvent.click(within(dialog).getByRole("button", { name: /Publish Grades/i }));

    await waitFor(() =>
      expect(publishGrades).toHaveBeenCalledWith({ assignment_id: "123", published: true })
    );
    await waitFor(() =>
      expect(screen.getByText("Unpublish Grades")).toBeInTheDocument()
    );
  });
});
