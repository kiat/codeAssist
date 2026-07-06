import { render, screen } from "@testing-library/react";
import ActionButtons from "../../../../pages/result/ActionButtons";

const handlers = {
  onRerun: jest.fn(),
  onUpload: jest.fn(),
  onResubmitEditor: jest.fn(),
  onDownload: jest.fn(),
  onHistoryOpen: jest.fn(),
};

describe("ActionButtons resubmit methods", () => {
  it("shows both resubmit options when file upload and code editor are enabled", () => {
    render(
      <ActionButtons
        {...handlers}
        isStudent
        allowFileUpload
        enableCodeEditor
      />
    );

    expect(
      screen.getByRole("button", { name: /resubmit via upload/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /resubmit via editor/i })
    ).toBeInTheDocument();
  });

  it("shows only file resubmit when only file upload is enabled", () => {
    render(
      <ActionButtons
        {...handlers}
        isStudent
        allowFileUpload
        enableCodeEditor={false}
      />
    );

    expect(
      screen.getByRole("button", { name: /resubmit via upload/i })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /resubmit via editor/i })
    ).not.toBeInTheDocument();
  });

  it("uses the same default style for upload and editor resubmit buttons", () => {
    render(
      <ActionButtons
        {...handlers}
        isStudent
        allowFileUpload
        enableCodeEditor
      />
    );

    const uploadButton = screen.getByRole("button", {
      name: /resubmit via upload/i,
    });
    const editorButton = screen.getByRole("button", {
      name: /resubmit via editor/i,
    });

    expect(uploadButton).not.toHaveClass("ant-btn-primary");
    expect(editorButton).not.toHaveClass("ant-btn-primary");
  });
});
