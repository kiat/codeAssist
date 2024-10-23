import { Button, message, Form, Modal, Upload } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import { useState, useContext } from "react";
import { GlobalContext } from "../../App";
import { useNavigate } from "react-router-dom";

export default function AssignmentModal({
  open,
  onCancel,
  assignmentID,
  assignmentTitle,
  late,
}) {
  const [file, setFile] = useState(null);
  const { userInfo } = useContext(GlobalContext);
  const navigate = useNavigate();

  const handleFileChange = (info) => {
    if (info.file.status === "done") {
      setFile(info.file.originFileObj);
      message.success(`${info.file.name} file uploaded successfully.`);
    } else if (info.file.status === "error") {
      message.error(`${info.file.name} file upload failed.`);
    }
  };

  const handleSubmit = async () => {
    console.log("ASSIGNMENT_MODAL");
    if (!file) {
      message.error("No file uploaded");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("assignment", assignmentTitle);
    formData.append("student_id", userInfo.id);
    formData.append("assignment_id", assignmentID);
    formData.append("late", late);

    try {
      const response = await fetch(
        process.env.REACT_APP_API_URL + "/upload_submission",
        {
          method: "POST",
          body: formData,
        }
      );

      // if (!response.ok) {
      //   throw new Error("Network response was not ok");
      // }

      const responseData = await response.json();
      navigateToResults(responseData.submissionID);
    } catch (error) {
      console.error("Error uploading file:", error);
      message.error("Failed to upload file. Please try again.");
    }
  };

  const navigateToResults = (submissionID) => {
    //use the returned submission id to navigate to its reults
    navigate(`/assignmentResult/${submissionID}`);

    // using updated route def
    //navigate(`/assignmentResult/${assignmentID}/${userInfo.id}`);
  };

  return (
    <Modal
      title="Submit Assignment"
      open={open}
      onCancel={onCancel}
      footer={null}
    >
      <Form layout="vertical">
        <Form.Item name="upload">
          <Upload.Dragger
            name="file"
            multiple={false}
            onChange={handleFileChange}
            beforeUpload={(file) => {
              setFile(file); // Set file on beforeUpload instead of upload itself
              return false; // Prevent default upload
            }}
            onDrop={(e) => console.log("Dropped files", e.dataTransfer.files)}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">
              Click or drag file to this area to upload
            </p>
          </Upload.Dragger>
        </Form.Item>
        {late && (
          <Form.Item style={{ marginTop: -10, marginBottom: 0 }}>
            <p
              style={{
                textAlign: "center",
                color: "#e10b0b",
                fontWeight: "bold",
              }}
            >
              Submission will be marked as late
            </p>
          </Form.Item>
        )}
        <Form.Item>
          <Button
            style={{ width: "100%" }}
            type="primary"
            onClick={handleSubmit}
          >
            Submit
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
}
