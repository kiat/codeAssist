import { Modal, Table, message, Button } from "antd";
import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function SubmissionHistoryModal({ open, onCancel, studentId, assignmentId, studentName, extra, currSubData }) {
  const [submissions, setSubmissions] = useState([]);
  const [confirmModalVisible, setConfirmModalVisible] = useState(false);
  const [submissionToSetDefault, setSubmissionToSetDefault] = useState(null);
  const [activeSubmission, setActiveSubmission] = useState();
  const [hasRequest, setHasRequest] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (open) {
      getSubmissions();
      getActive();
    }
  }, [open, studentId, assignmentId]);

  const getSubmissions = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL}/get_submissions`, {
        params: { student_id: studentId, assignment_id: assignmentId },
      });
      // If you need to show the highest scored submission as active, sort the data here
      // Sort by score descending and submission time ascending to get the latest highest score on top
      const sortedSubmissions = response.data.sort((a, b) => /*b.score - a.score ||*/ new Date(b.submitted_at) - new Date(a.submitted_at));
      setSubmissions(sortedSubmissions);
    } catch (error) {
      message.error("Failed to fetch submission history");
    }
  };
  const getActive = async () => {
    try {
      const submissionResponse = await fetch(`${process.env.REACT_APP_API_URL}/get_active_submission?student_id=${studentId}&assignment_id=${assignmentId}`);
      const submissionData = await submissionResponse.json();
      console.log(submissionData)
      console.log(submissionData.id)
      setActiveSubmission(submissionData.id)
      const req = await fetch(
        `${process.env.REACT_APP_API_URL}/check_regrade_request`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            submission_id: submissionData.id,
          }),
        }
      );
      // const req = await axios.post(`${process.env.REACT_APP_API_URL}/check_regrade_request`, {
      //   submission_id: submissionData.id,
      // });
      const reqData = await req.json();
      console.log("this is the response data:", reqData.has_request)
      setHasRequest(reqData.has_request)
    } catch(error){
      message.error("Failed")
    }
  }

  const handleSetDefaultSubmission = async (submissionId, e) => {
    e.stopPropagation();
    console.log("testing")
    try {
      console.log("hello", activeSubmission)
      if (hasRequest) {
        console.log("request")
        setSubmissionToSetDefault(submissionId);
        setConfirmModalVisible(true);
      } else {
        console.log("hello")
        await handleActivateSubmission(submissionId);
      }
    } catch (error) {
      message.error("Failed to check regrade request");
    }
  };

  const handleConfirm = async () => {
    if (submissionToSetDefault) {
      try {
        console.log("deleting regarde request ", activeSubmission)
        const req = await fetch(
          `${process.env.REACT_APP_API_URL}/delete_regrade_request`,
          {
            method: "POST",
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
        await handleActivateSubmission(submissionToSetDefault);
      } catch (error) {
        message.error("Failed to delete regrade request");
      }
    }
    setConfirmModalVisible(false);
  };

  const handleActivateSubmission = async (submissionId) => {
    try {
      //wait to check if the active submission has a regarde request --> if it does then display modal, if it doesn't proceed
      //modal should ask the user if tehy would like to delete the asscoiated regarde request and if confirmed should deleet that regrade reuqest form everywhere. 
      await axios.post(`${process.env.REACT_APP_API_URL}/activate_submission`, {
        submission_id: submissionId,
        student_id: studentId,
        assignment_id: assignmentId,
      });
      message.success("Submission activated successfully");
      await getSubmissions();
      //cancel this
      //reload
      navigate(`/assignmentResult/${submissionId}`);
      extra()
    } catch (error) {
      message.error("Failed to activate submission");
    }
  };

  const columns = [
    {
      title: '#',
      dataIndex: 'submission_number',
      key: 'submission_number',
    },
    {
      title: 'Submitted On',
      dataIndex: 'submitted_at',
      key: 'submitted_at',
      render: text => new Date(text).toLocaleString()
    },
    {
      title: 'Submitters',
      key: 'submitters',
      render: () => studentName
    },
    {
      title: 'Score',
      dataIndex: 'score',
      key: 'score',
    },
    {
      title: 'Active',
      key: 'active',
      //new redner to only render the checkmark when the submission is actually active accoridng to the database
      render: (text, record) => record.active? "✓": <Button onClick={(e) => handleSetDefaultSubmission(record.id, e)}>Activate</Button>
      //render: (text, record, index) => submissions.length && index === 0 ? "✓" : "" 
    },
  ];

  const onRowClick = (record) => {
    if (record.id !== currSubData.id) {
      navigate(`/assignmentResult/${record.id}`);
      extra();
    }
  }; 

  return (
    <Modal
      title="Submission History"
      open={open}
      onCancel={onCancel}
      footer={null}
      width={600}
    >
      <Table
        columns={columns}
        dataSource={submissions}
        rowKey="id"
        pagination={false}
        onRow={(record) => ({
          onClick: () => onRowClick(record),
          style: { cursor: 'pointer', backgroundColor: record.id === currSubData.id ? '#e6f7ff' : '' },
        })}
      />
       <Modal
        title="Confirm Change Default Submission"
        open={confirmModalVisible}
        onOk={handleConfirm}
        onCancel={() => setConfirmModalVisible(false)}
      >
        <p>Changing the default submission will delete the existing regrade request for the current default submission. Do you want to proceed?</p>
      </Modal>
    </Modal>
  );
}
