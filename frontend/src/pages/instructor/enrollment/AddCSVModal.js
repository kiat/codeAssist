import React, { useState } from "react";
import { Button, Form, Modal, Space, Upload, message } from "antd";
import { InboxOutlined } from "@ant-design/icons"
import LoadingOverlay from "../../../components/LoadingOverlay";

const AddCSVModal = ({ open, toggleAddCSVModalOpen, finishCSVForm , getEnrollment}) => {
  const [fileList, setFileList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [failedList, setFailedList] = useState([]);

  const maxMB = 101 // limit in MB
  const maxSize = maxMB * 1024 * 1024; // limit in bytes

  const handleFileChange = (info) => {
    let newFileList = [...info.fileList];

    // Limit the number of uploaded files
    newFileList = newFileList.slice(-1);

    // Only keep the last uploaded file
    setFileList(newFileList);

    if (info.file.status === "done") {
      message.success(`${info.file.name} file uploaded successfully`);
    } else if (info.file.status === "error") {
      message.error(`${info.file.name} file upload failed.`);
    }
  };

  const handleBeforeUpload = (file) => {
    // require csv file format
    const isCSV = file.type === "text/csv" || file.name.endsWith(".csv");
    if (!isCSV) {
      message.error("You can only upload CSV file!");
      return Upload.LIST_IGNORE;
    }

    // limit file size on upload
    if (file.size > maxSize) {
      message.error(`File must be smaller than ${maxMB}MB!`);
      return Upload.LIST_IGNORE;
    }

    return true;
  };

  const handleFinish = async () => {
    if (fileList.length === 0) {
      message.error("Please upload a CSV file");
      return;
    }
    const formData = new FormData();
    formData.append("file", fileList[0].originFileObj);
    
    setLoading(true);

    try {
      const result = await finishCSVForm(formData);
      const failed = result?.failed_enrollments ?? [];
      if (failed.length === 0) {
        message.success("All students enrolled successfully.");
        toggleAddCSVModalOpen();
        setFileList([]);
      } else {
        setFailedList(failed);
        getEnrollment();
      }
    } catch(error) {
      console.error("Error processing enrollments:", error);
      message.error("An error occurred while processing enrollments.");
    } finally {
      setLoading(false);
    }
  }

  const handleCancel = () => {
    toggleAddCSVModalOpen();
    setFileList([]);
    setFailedList([]);
  }

  return (
    <>
    <LoadingOverlay loading={loading}/>
    <Modal open={open} title="Add a User With CSV file" footer={null} onCancel={handleCancel}>
      <Form layout="vertical" onFinish={handleFinish}>
        <p style={{ marginBottom: 8, color: "#595959" }}>
          Upload a CSV with a header row. The <b>Email</b> column is required.
          Optionally include <b>Name</b>, <b>EID</b>, and <b>Role</b> columns.
        </p>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, fontFamily: "monospace", marginBottom: 16 }}>
          <thead>
            <tr style={{ background: "#e8e8e8" }}>
              {["Name", "Email", "EID", "Role"].map(col => (
                <th key={col} style={{ border: "1px solid #d9d9d9", padding: "4px 8px", textAlign: "left", fontWeight: 600 }}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr style={{ background: "#fafafa" }}>
              {["Jane Doe", "jdoe@university.edu", "12345678", "student"].map((val, i) => (
                <td key={i} style={{ border: "1px solid #d9d9d9", padding: "4px 8px" }}>
                  {val}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
        <Form.Item label={`Upload File (${maxMB}MB limit)`} name = "file">
          <Upload.Dragger
            name="file"
            multiple={false}
            fileList={fileList}
            onChange={handleFileChange}
            beforeUpload={handleBeforeUpload}
            customRequest={({ file, onSuccess }) => {
              setTimeout(() => {
                onSuccess("ok");
              }, 0);
            }}
            onDrop={e => console.log('Dropped files', e.dataTransfer.files)}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file here to upload CSV File</p>
          </Upload.Dragger>
        </Form.Item>
        {failedList.length > 0 && (
          <div style={{ marginBottom: 16, background: "#fff2f0", border: "1px solid #ffccc7", borderRadius: 4, padding: "8px 12px" }}>
            <p style={{ marginBottom: 6, fontWeight: 600, color: "#cf1322" }}>
              {failedList.length} email(s) could not be enrolled:
            </p>
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {failedList.map((f, i) => (
                <li key={i} style={{ fontSize: 13, color: "#434343" }}>
                  <b>{f.email}</b> — {f.reason}
                </li>
              ))}
            </ul>
          </div>
        )}
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">
              Submit
            </Button>
            <Button type="primary" danger onClick={handleCancel}>
              Cancel
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
    </>
  );
};

export default AddCSVModal;