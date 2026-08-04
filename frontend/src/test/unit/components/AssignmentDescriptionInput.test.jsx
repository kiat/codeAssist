import React from "react";
import { Form } from "antd";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AssignmentDescriptionInput from "../../../components/AssignmentDescriptionInput";

function Harness() {
  const [form] = Form.useForm();

  return (
    <Form form={form} initialValues={{ description: "" }}>
      <AssignmentDescriptionInput form={form} />
    </Form>
  );
}

describe("AssignmentDescriptionInput", () => {
  const originalFileReader = global.FileReader;

  afterEach(() => {
    global.FileReader = originalFileReader;
  });

  it("renders a pasteable description field and text upload control", () => {
    render(<Harness />);

    expect(screen.getByLabelText(/assignment description/i)).toBeInTheDocument();
    expect(screen.getByText("Upload .txt or .md")).toBeInTheDocument();
  });

  it("imports supported text files into the description field", async () => {
    const user = userEvent.setup();

    global.FileReader = class {
      readAsText() {
        this.result = "Imported assignment requirements.";
        this.onload();
      }
    };

    const { container } = render(<Harness />);
    const fileInput = container.querySelector("input[type='file']");

    await user.upload(
      fileInput,
      new File(["Imported assignment requirements."], "requirements.md", {
        type: "text/markdown",
      })
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/assignment description/i)).toHaveValue(
        "Imported assignment requirements."
      );
    });
  });
});
