import { Button, Form, message, Modal, Upload } from "antd";
import { InboxOutlined } from '@ant-design/icons';
import { useState, useContext, useEffect } from "react";
import { GlobalContext } from "../App";
import { useNavigate } from "react-router-dom";
import LoadingOverlay from './LoadingOverlay'; // Import the LoadingOverlay component
import { uploadSubmission } from "../services/submission";

// changes made for resubmit functionality
/**
 * file upload windows modal
 * @param {*} param0
 * @returns
 */
export default function UploadModal({
  open,
  title,
  onCancel,
  afterUpdate,
  url,
  data,
  assignmentID,
  assignmentTitle,
  extra
}) {
  const [file, setFile] = useState(null);
  const { userInfo } = useContext(GlobalContext);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false); // State for loading overlay
  const [confirmModalVisible, setConfirmModalVisible] = useState(false);
  const [activeSubmission, setActiveSubmission] = useState();
  const [hasRequest, setHasRequest] = useState(false);
  const [fileList, setFileList] = useState([]);

  useEffect(() => {
    if (!open) {
      setFileList([]);
      setFile(null);
      return;
    }

    if (open && userInfo?.id && assignmentID) {
      getActive();
    }
  }, [open, userInfo?.id, assignmentID]);

  const getActive = async () => {
    try {
      const submissionResponse = await fetch(
        `${process.env.REACT_APP_API_URL}/get_active_submission?student_id=${userInfo.id}&assignment_id=${assignmentID}`,
        { credentials: "include" }
      );
      if (!submissionResponse.ok) {
        setActiveSubmission(null);
        setHasRequest(false);
        return;
      }

      const submissionData = await submissionResponse.json();
      const submissionId = submissionData?.id ?? null;
      setActiveSubmission(submissionId);

      if (!submissionId) {
        setHasRequest(false);
        return;
      }

      const req = await fetch(
        `${process.env.REACT_APP_API_URL}/check_regrade_request`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            submission_id: submissionId,
          }),
        }
      );
      const reqData = await req.json();
      setHasRequest(Boolean(reqData?.has_request));
    } catch(error){
      setActiveSubmission(null);
      setHasRequest(false);
      message.error("Failed")
    }
  }


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

    if (hasRequest){
      setConfirmModalVisible(true);
    }
    else {
      finallySubmit();
    }

    console.log("these are the assignmnet details from the upload modal", assignmentID, assignmentTitle);
  };


  const navigateToResults = (submissionID) => {
    onCancel?.();
    navigate(`/assignmentResult/${submissionID}`);
    extra?.();
  };

  const handleConfirm = async () => {
    if (activeSubmission) {
      try {
        console.log("deleting regarde request ", activeSubmission)
        const req = await fetch(
          `${process.env.REACT_APP_API_URL}/delete_regrade_request`,
          {
            method: "POST",
            credentials: "include",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              submission_id: activeSubmission,
            }),
          }
        );
        console.log(req);
        message.success("Deleted successfully")
        finallySubmit();
      } catch (error) {
        message.error("Failed to delete regrade request");
      }
    }
    setConfirmModalVisible(false);
  };

  const finallySubmit = async () => {
    try {

      const formData = new FormData();
      formData.append('file', file);
      formData.append('assignment', assignmentTitle);
      formData.append('student_id', userInfo.id);
      formData.append('assignment_id', assignmentID);
      
      setLoading(true); // Show loading overlay
      const response = await uploadSubmission(formData)
      const responseData = response.data;
      setFileList([]);
      setFile(null);

      // Proceed to results page after successful upload
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
      setLoading(false); // Hide loading overlay
    }
  }


  return (
    //working on adding resubmit feature
    <>
    <LoadingOverlay loading={loading} /> 
    <Modal title="Submit Assignment" open={open} onCancel={onCancel} footer={null}>
      <Form layout="vertical">
        <Form.Item
          name="upload"
          valuePropName="fileList"
          getValueFromEvent={(info) => Array.isArray(info.fileList) ? info.fileList : []}
        >
          <Upload.Dragger
            name="file"
            multiple={false}
            fileList={fileList}
            onChange={handleFileChange}
            beforeUpload={file => {
              setFile(file);
              setFileList([{ uid: file.uid || `${Date.now()}`, name: file.name, status: 'done', originFileObj: file }]);
              return false; // Prevent default upload
            }}
            onDrop={e => console.log('Dropped files', e.dataTransfer.files)}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file to this area to upload</p>
          </Upload.Dragger>
        </Form.Item>
        <Form.Item>
          <Button style={{ width: "100%" }} type="primary" onClick={handleSubmit}>
            Submit
          </Button>
        </Form.Item>
      </Form>
      <Modal
        title="Confirm Change Default Submission"
        open={confirmModalVisible}
        onOk={handleConfirm}
        onCancel={() => setConfirmModalVisible(false)}
      >
        <p>Changing the default submission will delete the existing regrade request for the current default submission. Do you want to proceed?</p>
      </Modal>
    </Modal>
    </>
  );
}
