import { Card, Descriptions, PageHeader, Table, Button, message} from "antd";
import { useContext, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { GlobalContext } from "../../App";
import moment from "moment";
import AssignmentModal from "./assignment_modal";

export default function Assignments() {
  const [courseAssignment, setCourseAssignment] = useState([]);
  const urlParams = useParams();
  const navigate = useNavigate();
  const { userInfo, courseInfo } = useContext(GlobalContext);
  const [isModalOpen, setModalOpen] = useState(false);
  const [assignmentID, setAssignmentID] = useState("");
  const [assignmentTitle, setAssignmentTitle] = useState("");

  const columns = [
    {
      title: "NAME",
      dataIndex: "name",
      key: "name",
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (text, record) => (
        <Button type="link" onClick={() => handleAssignmentInteraction(record)}>
          {text}
        </Button>
      ),
    },
    {
      title: "STATUS",
      dataIndex: "submitted",
      key: "submitted",
      render: submitted => submitted ? "Completed" : "Unsubmitted",
      sorter: (a, b) => a.submitted - b.submitted,
    },
    {
      title: "GRADES",
      dataIndex: "score",
      key: "score",
      render: score => score !== null ? score : "-",
      sorter: (a, b) => (a.score || 0) - (b.score || 0),
    },
    {
      title: "RELEASED",
      dataIndex: "published_date",
      key: "published_date",
      render: text => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
      sorter: (a, b) => moment(a.published_date).unix() - moment(b.published_date).unix(),
    },
    {
      title: "DUE(CDT)",
      dataIndex: "due_date",
      key: "due_date",
      render: text => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
      sorter: (a, b) => moment(a.due_date).unix() - moment(b.due_date).unix(),
    },
  ];

  useEffect(() => {
    const fetchCourseAssignments = async () => {
      if (!userInfo || !userInfo.id) {
        navigate('/');
        return;
      }

      try {
        const assignmentsResponse = await fetch(
          `${process.env.REACT_APP_API_URL}/get_course_assignments?` +
          new URLSearchParams({ course_id: urlParams.courseId })
        );
        const assignmentsData = await assignmentsResponse.json();

        const updatedAssignments = await Promise.all(assignmentsData.map(async (assignment) => {
          try {
            const activeSubmissions = await fetch(`${process.env.REACT_APP_API_URL}/get_active_submission?` + new URLSearchParams({student_id: userInfo.id, assignment_id: assignment.id}))
            const activeData = await activeSubmissions.json();
            const submitted = activeData.completed;
            const score = submitted ? activeData.score : null;
            const submissionId = activeData.id;
            return {
              ...assignment,
              submitted,
              score,
              submissionId,
            };
          } catch (error) {
            console.error("Error fetching submission data:", error);
            return {
              ...assignment,
              submitted: false,
              score: null,
              submissionId: null,
            };
          }
        }));

        setCourseAssignment(updatedAssignments);
      } catch (error) {
        message.error('Failed to fetch assignments data.');
        console.error('Error fetching assignments:', error);
      }
    };

    fetchCourseAssignments();
  }, [urlParams.courseId, userInfo, navigate]);

  const handleAssignmentInteraction = (assignment) => {
    const now = moment();
    const dueDateTime = moment(assignment.due_date).valueOf();

    const isSubmitted = assignment.submitted;
    const dueDateHasPassed = now.isAfter(dueDateTime);

    if (isSubmitted) {
      //navigate(`/assignmentresult/${assignment.id}`);
      //navigate(`/assignmentresult/${assignment.id}/${userInfo.id}`);
      //latest route def
      navigate(`/assignmentresult/${assignment.submissionId}`);
    } else if (!dueDateHasPassed) {
      setModalOpen(true);
      setAssignmentTitle(assignment.name);
      setAssignmentID(assignment.id);
    } else if (dueDateHasPassed){
      message.error("Due Date Has Passed");
    }
  };

  const closeModal = () => {
    setModalOpen(false);
  };

  return (
    <>
      <PageHeader
        title={courseInfo.name}
        subTitle={`${courseInfo.semester} ${courseInfo.year}`}
        style={{ borderBottom: "1px solid #f0f0f0" }}
      >
        <Descriptions>
          <Descriptions.Item label="Course ID">{urlParams.courseId}</Descriptions.Item>
        </Descriptions>
      </PageHeader>

      <Card bordered={false}>
        <Table
          columns={columns}
          dataSource={courseAssignment}
          rowKey="id"
        />
      </Card>

      <AssignmentModal
        open={isModalOpen}
        onCancel={closeModal}
        assignmentID={assignmentID}
        assignmentTitle={assignmentTitle}
      />
    </>
  );
}