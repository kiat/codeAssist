import { Alert, Button, message, Form, Modal, Upload, Space, Typography } from "antd";
import { InboxOutlined, CodeOutlined } from '@ant-design/icons';
import { useState, useContext } from "react";
import { GlobalContext } from "../../App";
import { useNavigate } from "react-router-dom";
import { uploadSubmission } from "../../services/submission";
import LoadingOverlay from "../../components/LoadingOverlay";

export default function AssignmentModal({ open, onCancel, assignmentID, assignmentTitle, allowFileUpload = true, enableCodeEditor }) {
  const [file, setFile] = useState(null);
  const [fileList, setFileList] = useState([]);
  const { userInfo } = useContext(GlobalContext);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (info) => {
    const nextFileList = Array.isArray(info.fileList) ? info.fileList.slice(-1) : [];
    setFileList(nextFileList);

    if (info.file.status === 'done') {
      setFile(info.file.originFileObj || info.file);
      message.success(`${info.file.name} file uploaded successfully.`);
    } else if (info.file.status === 'error') {
      message.error(`${info.file.name} file upload failed.`);
    } else if (info.file.status === 'removed') {
      setFile(null);
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      message.error("No file uploaded");
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('assignment', assignmentTitle);
    formData.append('student_id', userInfo.id);
    formData.append('assignment_id', assignmentID);

    try {
      setLoading(true);
      const response = await uploadSubmission(formData)
      const responseData = response.data;
      navigateToResults(responseData.submissionID);
    } catch (error) {
      console.error("Error uploading file:", error);

      // check if we had a submission timeout error
      if (error.response && error.response.data.submission_id) {
        // Navigate to results if submission_id is in the response data
        navigateToResults(error.response.data.submission_id);
      }
    }
    finally {
      setLoading(false);
    }
  };

  const navigateToResults = (submissionID) => {
    navigate(`/assignmentResult/${submissionID}`);
  };

  const handleOpenEditor = () => {
    onCancel();
    navigate(`/codeEditor/${assignmentID}`);
  };

  const bothEnabled = allowFileUpload && enableCodeEditor;
  const neitherEnabled = !allowFileUpload && !enableCodeEditor;

  return (
    <>
    <LoadingOverlay loading={loading}/> 

    <Modal title="Submit Assignment" open={open} onCancel={onCancel} footer={null} width={520}>
      <div style={{ marginBottom: 20 }}>
        {neitherEnabled ? (
          <Alert
            type="warning"
            showIcon
            message="No Submission Methods Available"
            description="This assignment does not currently accept submissions. Please contact your instructor."
          />
        ) : (
          <>
            <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
              {bothEnabled ? "Choose how you want to submit your work:" : "Submit your work below:"}
            </Typography.Text>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {enableCodeEditor && (
                <>
                  <Button
                    block
                    size="large"
                    icon={<CodeOutlined />}
                    onClick={handleOpenEditor}
                    style={{ height: 56, textAlign: 'left', display: 'flex', alignItems: 'center' }}
                  >
                    <div style={{ marginLeft: 8 }}>
                      <div style={{ fontWeight: 600 }}>Open Code Editor</div>
                      <div style={{ fontSize: 12, color: '#999' }}>Type your code directly with auto-save</div>
                    </div>
                  </Button>
                  {bothEnabled && <div style={{ textAlign: 'center', color: '#999', fontSize: 12 }}>— or —</div>}
                </>
              )}
              {allowFileUpload && (
                <Form layout="vertical" style={{ marginBottom: 0 }}>
                  <Form.Item name="upload" style={{ marginBottom: 8 }}>
                    <Upload.Dragger
                      name="file"
                      multiple={false}
                      onChange={handleFileChange}
                      beforeUpload={file => {
                        setFile(file);
                        return false;
                      }}
                      onDrop={e => console.log('Dropped files', e.dataTransfer.files)}
                    >
                      <p className="ant-upload-drag-icon">
                        <InboxOutlined />
                      </p>
                      <p className="ant-upload-text">{enableCodeEditor ? "Upload a file instead" : "Click or drag file to upload"}</p>
                    </Upload.Dragger>
                  </Form.Item>
                  <Form.Item style={{ marginBottom: 0 }}>
                    <Button style={{ width: "100%" }} type="primary" onClick={handleSubmit} disabled={!file}>
                      Submit
                    </Button>
                  </Form.Item>
                </Form>
              )}
            </Space>
          </>
        )}
      </div>

    </Modal>
    </>
  );
}
