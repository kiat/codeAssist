import { Card, Descriptions, PageHeader, Table, Button, message } from "antd";
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
  const [isLate, setIsLate] = useState(false);

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
      render: (submitted, record) => {
        if (submitted) {
          if (record.late) {
            return <span style={{ color: "#e10b0b " }}>LATE</span>;
          }
          return "Completed";
        }
        return "Unsubmitted";
      },
      sorter: (a, b) => a.submitted - b.submitted,
    },
    {
      title: "GRADES",
      dataIndex: "score",
      key: "score",
      render: (score) => (score !== null ? score : "-"),
      sorter: (a, b) => (a.score || 0) - (b.score || 0),
    },
    {
      title: "RELEASED",
      dataIndex: "published_date",
      key: "published_date",
      render: (text) => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
      sorter: (a, b) =>
        moment(a.published_date).unix() - moment(b.published_date).unix(),
    },
    {
      title: "DUE (CDT)",
      dataIndex: "due_date",
      key: "due_date",
      render: (text) => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
      sorter: (a, b) => moment(a.due_date).unix() - moment(b.due_date).unix(),
    },
    {
      title: "LATE ALLOWED",
      dataIndex: "late_submission",
      key: "late_submission",
      render: (value) => (value ? "Yes" : "No"),
      sorter: (a, b) =>
        a.late_submission === b.late_submission
          ? 0
          : a.late_submission
          ? -1
          : 1,
    },
    {
      title: "LATE DUE (CDT)",
      dataIndex: "late_due_date",
      key: "late_due_date",
      render: (text) => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
      sorter: (a, b) => moment(a.due_date).unix() - moment(b.due_date).unix(),
    },
  ];

  useEffect(() => {
    const fetchAssignmentExtensions = async (assignment_id) => {
      try {
        const extensionResponse = await fetch(
          `${process.env.REACT_APP_API_URL}/get_extension?` +
            new URLSearchParams({
              student_id: userInfo.id,
              assignment_id: assignment_id,
            })
        );
        const extensionData = await extensionResponse.json();
        return extensionData;
      } catch (error) {
        message.error("Failed to fetch extension data.");
        console.error("Error fetching extensions:", error);
      }
    };
    const fetchCourseAssignments = async () => {
      if (!userInfo || !userInfo.id) {
        navigate("/");
        return;
      }

      try {
        console.log(
          `${process.env.REACT_APP_API_URL}/get_course_assignments?` +
            new URLSearchParams({ course_id: urlParams.courseId })
        );
        const assignmentsResponse = await fetch(
          `${process.env.REACT_APP_API_URL}/get_course_assignments?` +
            new URLSearchParams({ course_id: urlParams.courseId })
        );
        const assignmentsData = await assignmentsResponse.json();

        const updatedAssignments = await Promise.all(
          assignmentsData.map(async (assignment) => {
            try {
              const extension = await fetchAssignmentExtensions(assignment.id);
              const activeSubmissions = await fetch(
                `${process.env.REACT_APP_API_URL}/get_active_submission?` +
                  new URLSearchParams({
                    student_id: userInfo.id,
                    assignment_id: assignment.id,
                  })
              );
              const activeData = await activeSubmissions.json();
              const submitted = activeData.completed;
              const score = submitted ? activeData.score : null;
              const submissionId = activeData.id;
              const late = activeData.late;
              if (extension.release_date_extension) {
                assignment.release_date = extension.release_date_extension;
              }
              if (extension.due_date_extension) {
                assignment.due_date = extension.due_date_extension;
              }
              if (extension.late_due_date_extension) {
                assignment.late_due_date = extension.late_due_date_extension;
                assignment.late_submission = true;
              }
              return {
                ...assignment,
                submitted,
                score,
                submissionId,
                late,
              };
            } catch (error) {
              console.error("Error fetching submission data:", error);
              return {
                ...assignment,
                submitted: false,
                score: null,
                submissionId: null,
                late: null,
              };
            }
          })
        );

        setCourseAssignment(updatedAssignments);
      } catch (error) {
        message.error("Failed to fetch assignments data.");
        console.error("Error fetching assignments:", error);
      }
    };

    fetchCourseAssignments();
  }, [urlParams.courseId, userInfo, navigate]);

  const handleAssignmentInteraction = (assignment) => {
    const now = moment();
    const dueDateTime = moment(assignment.due_date).valueOf();
    const lateDueDateTime = moment(assignment.late_due_date).valueOf();
    // const extension = await fetchAssignmentExtensions(assignment.id);
    // if (extension != null) {
    //   if (extension.due_date_extension) {
    //     dueDateTime = moment(extension.due_date_extension).valueOf();
    //   }
    //   if (extension.late_due_date_extension) {
    //     dueDateTime = moment(extension.late_due_date_extension).valueOf();
    //   }
    // }

    const isSubmitted = assignment.submitted;
    const dueDateHasPassed = now.isAfter(dueDateTime);
    const lateDueDateHasPassed = now.isAfter(lateDueDateTime);

    if (isSubmitted) {
      navigate(`/assignmentresult/${assignment.submissionId}`);
    } else if (!dueDateHasPassed) {
      setModalOpen(true);
      setAssignmentTitle(assignment.name);
      setAssignmentID(assignment.id);
      setIsLate(false);
    } else if (assignment.late_submission && !lateDueDateHasPassed) {
      setModalOpen(true);
      setAssignmentTitle(assignment.name);
      setAssignmentID(assignment.id);
      setIsLate(true);
    } else {
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
          <Descriptions.Item label="Course ID">
            {urlParams.courseId}
          </Descriptions.Item>
        </Descriptions>
      </PageHeader>

      <Card bordered={false}>
        <Table columns={columns} dataSource={courseAssignment} rowKey="id" />
      </Card>

      <AssignmentModal
        open={isModalOpen}
        onCancel={closeModal}
        assignmentID={assignmentID}
        assignmentTitle={assignmentTitle}
        late={isLate}
      />
    </>
  );
}
