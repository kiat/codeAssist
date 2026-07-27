import React from "react";
import { render, screen } from "@testing-library/react";
import Enrollment from "../../../../../pages/instructor/enrollment";
import { GlobalContext } from "../../../../../App";
import {
  getCourseEnrollment,
  createEnrollment,
  createEnrollmentCSV,
  updateRole,
} from "../../../../../services/course";
import { getUserByEmail } from "../../../../../services/user";

jest.mock("../../../../../services/course", () => ({
  getCourseEnrollment: jest.fn(),
  createEnrollment: jest.fn(),
  createEnrollmentCSV: jest.fn(),
  updateRole: jest.fn(),
}));

jest.mock("../../../../../services/user", () => ({
  getUserByEmail: jest.fn(),
}));

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useParams: () => ({ courseId: "course-1" }),
}));

const ROSTER = [
  { id: "student-1", name: "Alice", email_address: "alice@test.com", role: "student" },
  { id: "ta-1", name: "Bob", email_address: "bob@test.com", role: "ta" },
  { id: "instructor-1", name: "Carol", email_address: "carol@test.com", role: "instructor" },
];

function renderEnrollment(courseRole) {
  return render(
    <GlobalContext.Provider value={{ courseRole }}>
      <Enrollment />
    </GlobalContext.Provider>
  );
}

describe("Enrollment role-editing access control", () => {
  beforeEach(() => {
    getCourseEnrollment.mockResolvedValue({ data: ROSTER });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("shows no role-change affordance for any row when viewed by a TA", async () => {
    renderEnrollment("ta");

    await screen.findByText("Alice");

    // The role-change UI renders a down-arrow icon only on the editable path;
    // a TA should never see it, for any row (including other students).
    expect(document.querySelectorAll(".anticon-down").length).toBe(0);
  });

  it("lets an instructor change a student's or TA's role, but not another instructor's", async () => {
    renderEnrollment("instructor");

    await screen.findByText("Alice");
    await screen.findByText("Bob");
    await screen.findByText("Carol");

    // Student and TA rows are editable (down-arrow affordance present).
    expect(document.querySelectorAll(".anticon-down").length).toBe(2);
  });
});
