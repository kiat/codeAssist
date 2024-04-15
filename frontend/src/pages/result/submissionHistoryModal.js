import { Modal, Table, message } from "antd";
import { useEffect, useState } from "react";
import axios from "axios";

export default function SubmissionHistoryModal({ open, onCancel, studentId, assignmentId, studentName }) {
  const [submissions, setSubmissions] = useState([]);

  useEffect(() => {
    if (open) {
      getSubmissions();
    }
  }, [open, studentId, assignmentId]);

  const getSubmissions = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL}/get_submissions`, {
        params: { student_id: studentId, assignment_id: assignmentId },
      });
      // If you need to show the highest scored submission as active, sort the data here
      // Sort by score descending and submission time ascending to get the latest highest score on top
      const sortedSubmissions = response.data.sort((a, b) => b.score - a.score || new Date(a.submitted_at) - new Date(b.submitted_at));
      setSubmissions(sortedSubmissions);
    } catch (error) {
      message.error("Failed to fetch submission history");
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
      render: (text, record, index) => submissions.length && index === 0 ? "✓" : "" 
    },
  ];

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
      />
    </Modal>
  );
}
