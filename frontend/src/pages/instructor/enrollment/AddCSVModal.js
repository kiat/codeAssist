import React, { useState } from "react";
import { Button, Form, Modal, Space, Upload, message } from "antd";
import { InboxOutlined } from "@ant-design/icons"
import LoadingOverlay from "../../../components/LoadingOverlay";

const AddCSVModal = ({ open, toggleAddCSVModalOpen, finishCSVForm , getEnrollment}) => {
  const [fileList, setFileList] = useState([]);
  const [loading, setLoading]  = useState(false);

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
      await finishCSVForm(formData);
      message.success("Enrollments processed.");
      toggleAddCSVModalOpen();
      getEnrollment();
    } catch(error) {
      console.error("Error processing enrollments:", error);
      message.error("An error occurred while processing enrollments.");
    } finally {
      setLoading(false);
    }
    setFileList([]);
  }

  const handleCancel = () => {
    toggleAddCSVModalOpen();
    setFileList([]);
  }

  return (
    <>
    <LoadingOverlay loading={loading}/>
    <Modal open={open} title="Add a User With CSV file" footer={null} onCancel={handleCancel}>
      <Form layout="vertical" onFinish={handleFinish}>
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