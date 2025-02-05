import React, { useState } from "react";
import {
  Button,
  Form,
  Modal,
  Space,
  Upload,
  message
} from "antd";
import { InboxOutlined } from "@ant-design/icons"

const AddCSVModal = ({ open, toggleAddCSVModalOpen, finishCSVForm }) => {
  const [fileList, setFileList] = useState([]);

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
    const isCSV = file.type === "csv";
    if (!isCSV) {
      message.error("You can only upload CSV file!");
    }
    return isCSV;
  };

  const handleFinish = (values) => {
    finishCSVForm(values);
    setFileList([]);
  }

  const handleCancel = () => {
    toggleAddCSVModalOpen();
    setFileList([]);
  }

  return (
    <Modal
      open={open}
      title="Add a User With CSV file"
      footer={null}
      onCancel={handleCancel}
    >
      <Form layout="vertical" onFinish={handleFinish}>
        <Form.Item label="Upload" name = "file">
          <Upload.Dragger
            name="file"
            multiple={false}
            fileList={fileList}
            action="http://localhost:5001/upload_submission"
            onChange={handleFileChange}
            beforeUpload={handleBeforeUpload}
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
  );
};

export default AddCSVModal;