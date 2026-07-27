import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import RolePill from "../../../components/RolePill";

describe("RolePill", () => {
  it("renders the label for each known role, case-insensitively", () => {
    render(<RolePill role="instructor" />);
    expect(screen.getByText("Instructor")).toBeInTheDocument();

    render(<RolePill role="TA" />);
    expect(screen.getByText("TA")).toBeInTheDocument();

    render(<RolePill role="Student" />);
    expect(screen.getByText("Student")).toBeInTheDocument();
  });

  it("falls back to the raw role text for an unknown role", () => {
    render(<RolePill role="superadmin" />);
    expect(screen.getByText("superadmin")).toBeInTheDocument();
  });

  it("renders without crashing when role is missing", () => {
    render(<RolePill />);
    expect(document.querySelector("span")).toBeInTheDocument();
  });
});
