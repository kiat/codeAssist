import {
  Button,
  Card,
  Input,
  PageHeader,
  Space,
  Table,
  Typography,
  message,
} from "antd";
import {
  CloseOutlined,
  ReloadOutlined,
  RightOutlined,
} from "@ant-design/icons";
import PageContent from "../../components/layout/pageContent";
import PageBottom from "../../components/layout/pageBottom";
import RerunAutograderModal from "./RerunAutograderModal";
import { deleteSubmission } from "../../services/assignmentResult";
import { useContext, useState, useEffect } from "react";
import { GlobalContext } from "../../App";
import { useNavigate } from "react-router-dom";
import moment from "moment";

const SubmissionsManager = () => {
  const [rerunModalOpen, setRerunModalOpen] = useState(false);
  const { assignmentInfo, updateAssignmentInfo } = useContext(GlobalContext);
  const { courseInfo } = useContext(GlobalContext);
  const [tableData, setTableData] = useState([]);
  const [forceUpdate, setForceUpdate] = useState(0); // State to trigger re-fetching
  const navigate = useNavigate();

  const toggleRerunModalOpen = () => setRerunModalOpen(!rerunModalOpen);

  const goAssignmentResult = (name, id) => {
    //now accepting the student id to add into globalContext (so assignmnetResult can pull it)
    //console.log(name, id)
    updateAssignmentInfo({
      ...assignmentInfo,
      studentName: name,
      studentId: id,
    });
    //use new route
    navigate(`/assignmentResult/${assignmentInfo.id}/${id}`) 
    // navigate(`/assignmentResult/${assignmentInfo.id}`);
  };

  const funcDeleteSubmission = async (record) => {
    // const response = await fetch(
    //   `${process.env.REACT_APP_API_URL}/delete_submission?submission_id=${record.id}`,
    //   { method: "DELETE" }
    // );
    const response = deleteSubmission( { submission_id: record.id });
    if (response.ok) {
      // Increment forceUpdate to trigger a re-fetch of submissions
      setForceUpdate((u) => u + 1);
      message.success("Submission deleted successfully");
    } else {
      message.error("Failed to delete submission");
    }
  };

  const columns = [
    {
      title: "NAME",
      dataIndex: "name",
      render: (text, record) => {
        //decrypting teh new way we're represnting the name field in our table
        // Split the concatenated string into name and id
        const [name, id] = text.split("(");
        const studentId = id.replace(")", ""); // Remove the trailing ')'

        return (
          <Typography.Link
            onClick={() => goAssignmentResult(name.trim(), studentId.trim())}
          >
            {text}
          </Typography.Link>
        );
      },
      sorter: (a, b) => a.name.localeCompare(b.name),
      // title: "NAME",
      // dataIndex: "name",
      // render: (text, record) => <Typography.Link onClick={() => goAssignmentResult(text)}>{text}</Typography.Link>,
      // sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: "SUBMISSION TIME (CST)",
      dataIndex: "submissionTime",
      render: (text) => moment(text).format("MM/DD/YYYY HH:mm:ss"),
      sorter: (a, b) => a.submissionTime - b.submissionTime,
    },
    {
      title: "SCORE",
      dataIndex: "score",
      align: "center",
      sorter: (a, b) => a.score - b.score,
    },
    {
      title: "DELETE",
      align: "center",
      render: (_, record) => (
        <Button
          danger
          type="primary"
          size="small"
          icon={<CloseOutlined />}
          onClick={() => funcDeleteSubmission(record)}
        />
      ),
    },
  ];

  useEffect(() => {
    const fetchStudents = async () => {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/get_course_enrollment?course_id=${courseInfo.id}`
      );
      const students = await response.json();
      if (students && students.length > 0) {
        await fetchSubmissions(students);
      } else {
        setTableData([]);
      }
    };

    const fetchSubmissions = async (students) => {
      const submissions = await Promise.all(
        students.map(async (student) => {
          const response = await fetch(
            `${process.env.REACT_APP_API_URL}/get_latest_submission?student_id=${student.id}&assignment_id=${assignmentInfo.id}`
          );
          const data = await response.json();

          // Ensure that each submission has a non-null score, a name, and a submission time
          if (
            data &&
            data.submitted_at &&
            data.score !== undefined &&
            student.name
          ) {
            return {
              //apending both student name and student id so instructor side can access student results
              name: `${student.name} (${student.id})`, // You would need to adjust this if the name isn't in the 'students' variable
              submissionTime: moment(data.submitted_at).valueOf(),
              score: data.score,
              id: data.id, // This assumes that 'id' refers to the submission's unique identifier
            };
          }
          return null;
        })
      );

      // Filter out any null submissions and set the table data
      const validSubmissions = submissions.filter(
        (submission) => submission !== null
      );
      setTableData(validSubmissions);
    };

    if (assignmentInfo.id) {
      fetchStudents();
    }
  }, [courseInfo.id, assignmentInfo.id, forceUpdate]); // Add forceUpdate as a dependency

  return (
    <>
      <PageContent>
        <PageHeader title="Manage Submissions" />
        <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
          <Table columns={columns} dataSource={tableData} rowKey="id" />
        </Card>
      </PageContent>
      <PageBottom>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={toggleRerunModalOpen}>
            Regrade All Submissions
          </Button>
          <Button>
            <span>Grade Submissions</span>
            <RightOutlined />
          </Button>
        </Space>
      </PageBottom>
      <RerunAutograderModal
        open={rerunModalOpen}
        onCancel={toggleRerunModalOpen}
      />
    </>
  );
};

export default SubmissionsManager;
