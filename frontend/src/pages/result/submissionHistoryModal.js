import { Modal, Table, message } from "antd";
import axios from "axios";
import { useEffect, useState } from "react";
// import { columns } from "./constants"; 

export default function SubmissionHistoryModal({ open, onCancel, studentId, assignmentId }) {
  const [submissions, setSubmissions] = useState([]);

  useEffect(() => {
    if (open) {
      getSubmissions();
    }
  }, [open]);

  const getSubmissions = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL}/get_submissions`, {
        params: { student_id: studentId, assignment_id: assignmentId },
      });
      setSubmissions(response.data);
    } catch (error) {
      message.error("Failed to fetch submission history");
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
        // columns={columns}
        dataSource={submissions}
        rowKey="id"
        pagination={false}
      />
    </Modal>
  );
}
