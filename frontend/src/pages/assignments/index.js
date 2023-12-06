import { Card, Descriptions, PageHeader, Table, Button } from "antd";
import axios from "axios";
import { useCallback, useContext, useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { GlobalContext } from "../../App";
import moment from "moment";

import "../../mock/assignment";
import AssignmentModal from "./assignment_modal";

/**
 * course assignment modal
 * @returns
 */
export default function Assignments() {
  const [courseAssignment, setCourseAssignment] = useState([]);
  const urlParams = useParams();
  const { courseId } = urlParams;
  const navigate = useNavigate();
  const { userInfo, courseInfo } = useContext(GlobalContext);
  const location = useLocation();
  const [isModalOpen, setModalOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [assignmentID, setAssignmentID] = useState("")
  const [assignmentTitle, setAssignmentTitle] = useState("")


  const columns = [
    {
      title: "NAME",
      dataIndex: "name",
      key: "name",
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (text, record) => (
        <Button type="link" onClick={() => nameColLinkAction(record)}>
          {text}
        </Button>
      )
    },
    {
      title: "STATUS",
      dataIndex: "status",
      render: text => (text === 1 ? "Submitted" : "Not Submitted"),
      sorter: (a, b) => a.status - b.status,
    },
    {
      title: "GRADES",
      dataIndex: "grades",
      render: text => text || "-",
      sorter: (a, b) => a.grades - b.grades,
    },
    {
      title: "RELEASED",
      dataIndex: "published_date",
      render: text => {
        const publishedDate = moment(text).valueOf();
        const formattedDate = moment(text).format("MMM DD [AT] h:mmA").toUpperCase();
        return <span data-timestamp={publishedDate}>{formattedDate}</span>
      },
      sorter: (a, b) => a.released - b.released,
    },
    {
      title: "DUE(CDT)",
      dataIndex: "due_date",
      render: text => {
        const dueDate = moment(text).valueOf();
        const formattedDate = moment(text).format("MMM DD [AT] h:mmA").toUpperCase();
        return <span data-timestamp={dueDate}>{formattedDate}</span>;
      },
      sorter: (a, b) => a.due - b.due,
    },
  ];

  /**
   * This is how it was originally done, so I have left it here just in case
   * This functionality is now done through handleAssignmentAction
   */
  // const openModal = (assignment) => {
  //   const now = moment();
  //   const dueDateHasPassed = now.isAfter(moment(assignment.due_date));
  //   const isSubmitted = assignment.status === 1;

  //   if (isSubmitted) {
  //     // If the assignment has been submitted, navigate to the assignment results
  //     navigate(`/assignmentresult/${assignment.id}`);
  //   } else if (!dueDateHasPassed) {
  //     // If the assignment is not submitted and the due date has not passed, open the upload modal
  //     setModalOpen(true);
  //     setAssignmentTitle(assignment.name);
  //     setAssignmentID(assignment.id);
  //   }
  //   // If the assignment is not submitted and the due date has passed, do nothing
  // };

  /**
   * TODO: this may be deleted later once testing is fully done on the new nameColLinkAction
   */
  const closeModal = () => {
    setModalOpen(false);
  }
  // Function to handle the opening of the modal or navigation based on the assignment's state
  const nameColLinkAction = (assignment) => {
    const now = moment();
    const dueDateTime = moment(assignment.due_date).valueOf();

    const isSubmitted = assignment.status;
    const dueDateHasPassed = now.isAfter(dueDateTime);

    if (isSubmitted) {
      navigate(`/assignmentresult/${assignment.id}`);
    } else if (!dueDateHasPassed) {
      setModalOpen(true);
      setAssignmentTitle(assignment.name);
      setAssignmentID(assignment.id);
    }
    // If the due date has passed and it's not submitted, do nothing.
  };


  useEffect(() => {
    if (!userInfo || !userInfo.id) {
      navigate('/');
      return;
    }
    fetch(process.env.REACT_APP_API_URL + "/get_course_assignments?" +
      new URLSearchParams({ course_id: courseId }))
      .then(res => res.json())
      .then(async assignmentsData => {
        const updatedAssignments = await Promise.all(assignmentsData.map(async assignment => {
          let submissionStatus = 0; // default status (not submitted)
          let grade = "-"; // default grade

          try {
            const response = await fetch(
              process.env.REACT_APP_API_URL + "/get_latest_submission?" +
              new URLSearchParams({
                student_id: userInfo.id,
                assignment_id: assignment.id,
              })
            );
            const submissionData = await response.json();

            if (submissionData.length > 0 && submissionData[0].completed) {
              submissionStatus = 1; // submitted
              grade = submissionData[0].score;
            }
          } catch (error) {
            console.error("Error fetching submission data:", error);
          }

          return {
            ...assignment,
            status: submissionStatus,
            grades: grade,
          };
        }));

        setCourseAssignment(updatedAssignments);
      })
      .catch(error => {
        console.error("Error fetching course assignments:", error);
      });
  }, [courseId, userInfo.id]);



  return (
    <>
      <PageHeader
        title={courseInfo.name}
        subTitle={`${courseInfo.semester} ${courseInfo.year}`}
        style={{ borderBottom: "1px solid #f0f0f0" }}
      >
        <Descriptions>
          <Descriptions.Item label='Course ID'>
            {urlParams.courseId}
          </Descriptions.Item>
        </Descriptions>
      </PageHeader>

      <Card bordered={false}>
        {courseAssignment ? (
          <Table
            columns={
              columns
            }
            dataSource={courseAssignment.filter(assignment => assignment.published)}
            rowKey='id'
            onRow={(record) => {
              return {
                onClick: () => {
                  const now = Date.now();
                  const publishedDate = moment(record.published_date).valueOf();
                  const dueDate = moment(record.due_date).valueOf();
                  const isSubmitted = record.status

                  if (isSubmitted) {
                    navigate(`/assignmentresult/${record.id}`);
                  } else if (now <= dueDate) {
                    // Open modal to submit assignment since the due date has not passed and it's not submitted
                    setModalOpen(true);
                    setAssignmentTitle(record.name);
                    setAssignmentID(record.id);
                  }
                  // If not submitted and the due date has passed, do nothing.
                },
              };
            }}

          />
        ) : (
          <div>No assignments yet</div>
        )}
      </Card>
      <AssignmentModal open={isModalOpen} onCancel={closeModal} assignmentID={assignmentID} assignmentTitle={assignmentTitle} />
    </>
  );

}