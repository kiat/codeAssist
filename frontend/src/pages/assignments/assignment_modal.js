import { Button, message, Form, Modal, Upload } from "antd";
import { InboxOutlined } from '@ant-design/icons';
import { useState, useContext } from "react";
import { GlobalContext } from "../../App";
import { useNavigate } from "react-router-dom";

export default function AssignmentModal({ open, onCancel, submit, assignmentID, assignmentTitle}) {
  const [file, setFile] = useState(null);
  const { userInfo } = useContext(GlobalContext);

  const handleFileChange = (info) => {
    const { status, response } = info.file;
    if (status === 'done') {
      setFile(info.file);
      message.success(`${info.file.name} file uploaded successfully.`);
    } else if (status === 'error') {
      message.error(`${info.file.name} file upload failed.`);
    }
  };

  const handleBeforeUpload = (file) => {
    const formData = new FormData();

    formData.append('file', file);
    formData.append('assignment', assignmentTitle);
    formData.append('student_id', userInfo.id);
    formData.append('assignment_id', assignmentID);
    // formData.append('name', userInfo.name);
   
    fetch(process.env.REACT_APP_API_URL + "/upload_submission", {
      method: "POST",
      body: formData
    })
    .then((response) => response.json())
    .then((data) => {
      console.log(data)
      navigateToResults();
    })
    .catch((error) => {
      console.error("Error uploading file:", error);
    });

    return false;
  };

  const navigate = useNavigate();

  const navigateToResults = () => {
    navigate(`/assignmentResult/${assignmentID}`)
  }

  return (
    <Modal title="Submit Assignment" open={open} onCancel={onCancel} footer={null}>
      <Form layout="vertical">
        <Form.Item name="upload">
          <Upload.Dragger
            name="file"
            multiple={false}
            action={`${process.env.REACT_APP_API_URL}/upload_submission`}
            onChange={handleFileChange}
            beforeUpload={handleBeforeUpload}
            onDrop={e => console.log('Dropped files', e.dataTransfer.files)}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file to this area to upload</p>
          </Upload.Dragger>
        </Form.Item>
        <Form.Item>
          <Button style={{ width: "100%" }} type="primary" onClick={navigateToResults}>
            Submit
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
}


