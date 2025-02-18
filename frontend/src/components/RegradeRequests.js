import React, { useState, useEffect, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, Descriptions, PageHeader, Table, Typography, message } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import { GlobalContext } from '../App';

function RegradeRequests() {
  const { userInfo, courseInfo } = useContext(GlobalContext);
  const [requests, setRequests] = useState([]);

  useEffect(() => {
    const fetchRequests = async () => {
      try {
        console.log("course info:", courseInfo.id)
        const endpoint = userInfo.isStudent
          ? `${process.env.REACT_APP_API_URL}/get_student_regrade_requests?student_id=${userInfo.id}&course_id=${courseInfo.id}`
          : `${process.env.REACT_APP_API_URL}/get_instructor_regrade_requests?course_id=${courseInfo.id}`;

        const response = await fetch(endpoint);
        const data = await response.json();
        
        // Fetch the latest submission for each regrade request
        const requestsWithSubmissions = await Promise.all(data.map(async (request) => {
          const submissionResponse = await fetch(`${process.env.REACT_APP_API_URL}/get_active_submission?student_id=${request.studentId}&assignment_id=${request.assignmentId}`);
          // const submissionResponse = await fetch(
          //   `${process.env.REACT_APP_API_URL}/get_latest_submission?student_id=${request.studentId}&assignment_id=${request.assignmentId}`
          // );
          const submissionData = await submissionResponse.json();
          
          return {
            ...request,
            submissionId: submissionData.id // Add the latest submissionId
          };
        }));
        
        setRequests(requestsWithSubmissions);
      } catch (error) {
        console.error("Error fetching regrade requests:", error);
        message.error("Failed to fetch regrade requests");
      }
    };
    fetchRequests();
  }, [userInfo]);

  const columns = [
    {
      title: 'Assignment',
      dataIndex: 'assignmentName',
      key: 'assignmentName',
    },
    {
      title: 'Student',
      dataIndex: 'studentName',
      key: 'studentName',
    },
    {
      title: 'Justification',
      dataIndex: 'justification',
      key: 'justification',
    }, 
    {
      title: 'Reviewed',
      dataIndex: 'reviewed',
      key: 'reviewed',
      render: reviewed => (
        <CheckCircleOutlined style={{ color: reviewed ? 'green' : 'grey' }} />
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (text, record) => (
        <Link to={`/assignmentResult/${record.submissionId}`}>View Results</Link>
      ),
    }
  ];

  const studentColumns = columns.filter(col => col.key !== 'studentName');

  return (
    <div>
      <PageHeader title={"Regrade Requests"} style={{ borderBottom: "1px solid #f0f0f0" }}></PageHeader>
      <Card bordered={false}>
        <Table
          dataSource={requests}
          columns={userInfo.isStudent ? studentColumns : columns}
          rowKey="id"
        />
      </Card>
    </div>
  );
}

export default RegradeRequests;
