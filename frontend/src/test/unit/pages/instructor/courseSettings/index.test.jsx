import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import CourseSettings from "../../../../../pages/instructor/courseSettings";
import { GlobalContext } from "../../../../../App";
import {
  getCourseAssignments,
  getCourseInfo,
} from "../../../../../services/course";

jest.mock("../../../../../services/course", () => ({
  getCourseAssignments: jest.fn(),
  getCourseInfo: jest.fn(),
  updateCourse: jest.fn(),
  deleteCourse: jest.fn(),
  deleteAllAssignments: jest.fn(),
}));

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useParams: () => ({ courseId: "course-1" }),
  useNavigate: () => mockNavigate,
}));

function renderCourseSettings(courseRole = "instructor") {
  return render(
    <GlobalContext.Provider
      value={{ courseInfo: {}, updateCourseInfo: jest.fn(), courseRole }}
    >
      <CourseSettings />
    </GlobalContext.Provider>
  );
}

describe("CourseSettings access control", () => {
  beforeEach(() => {
    getCourseInfo.mockResolvedValue({ data: [{}] });
    getCourseAssignments.mockResolvedValue({ data: [] });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("does not redirect an instructor away from course settings", async () => {
    renderCourseSettings("instructor");

    await screen.findByText("Edit Course");

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it("redirects a TA away from course settings", async () => {
    renderCourseSettings("ta");

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/instructorDashboard/course-1");
    });
  });

  it("redirects a student away from course settings", async () => {
    renderCourseSettings("student");

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/instructorDashboard/course-1");
    });
  });
});
