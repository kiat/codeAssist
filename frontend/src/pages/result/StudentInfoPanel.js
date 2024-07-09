import { useState, useEffect, useContext, useRef } from "react";
import { Typography, Space, Button, Modal, Input, message } from "antd";
import { CheckCircleOutlined } from "@ant-design/icons";
import { GlobalContext } from "../../App";
import { useParams } from "react-router-dom";

export default function StudentInfoPanel({
  assignmentName,
  studentName,
  score,
  totalPoints,
  active,
}) {
  //if it is a student I want to display a button to submit a regrade request --> will take them to the add justification modal
  //if it is an instructor i want to be able to see the regarde request if it exists --> should have an edit butotn somewhere that opens a modal to chnage th student's grade
  const { userInfo } = useContext(GlobalContext);
  const [RequestModalVisible, setRequestModalVisible] = useState(false);
  const [EditGradeModalVisible, setEditGradeModalVisible] = useState(false);
  const [Grade, setGrade] = useState("");
  const [Justification, setJustification] = useState(null); // Initialize as null
  //const { assignmentId, studentId } = useParams();
  const [SubmissionId, setSubmissionId] = useState();
  const [highlight, setHighlight] = useState(false);
  const justificationRef = useRef(null);
  const [CheckColor, SetCheckColor] = useState("grey");
  const [isLoading, setIsLoading] = useState(true); // Loading state
  const [TempJustification, setTempJustification] = useState(null)
  const {submissionId} = useParams();
  const [infoShown, SetInfoShown] = useState(false)

  useEffect(() => {
    const fetchJustificationDetails = async () => {
      if (submissionId) {
        try {
          const response = await fetch(
            `${process.env.REACT_APP_API_URL}/get_regrade_request?` +
              new URLSearchParams({
                submission_id: submissionId,
              })
          );
          const request = await response.json();
          if (request.justification) {
            if (request.reviewed === true) {
              SetCheckColor("green");
            }
            if (userInfo.isStudent) {
              setJustification(request.justification);
            } else {
              setJustification(request.justification);
              if (request.reviewed === false) {
                setHighlight(true);
                setTimeout(() => setHighlight(false), 3000);
                if (!infoShown){
                  message.info("Regrade Request");
                  SetInfoShown(true);
                }
              }
            }
          } else {
            setJustification("");
          }
        } catch (error) {
          console.log(error);
        } finally {
          setIsLoading(false); // Set loading to false after fetching
        }
      } else {
        setIsLoading(false); // Set loading to false if no SubmissionId
      }
    };
    fetchJustificationDetails();
  },[submissionId, userInfo]);

  // useEffect(() => {
  //   const fetchSubmissionDetails = async () => {
  //     if (userInfo) {
  //       console.log(assignmentId, studentId);
  //       try {
  //         const response = await fetch(
  //           `${process.env.REACT_APP_API_URL}/get_latest_submission?` +
  //             new URLSearchParams({
  //               student_id: studentId,
  //               assignment_id: assignmentId,
  //             })
  //         );
  //         const submission = await response.json();
  //         console.log(submission.id);
  //         if (submission) {
  //           setSubmissionId(submission.id);
  //         }
  //       } catch (error) {
  //         console.log(error);
  //       }
  //     }
  //   };
  //   fetchSubmissionDetails();
  // }, [userInfo, assignmentId, studentId]);

  // useEffect(() => {
  //   const fetchJustificationDetails = async () => {
  //     if (SubmissionId) {
  //       try {
  //         const response = await fetch(
  //           `${process.env.REACT_APP_API_URL}/get_regrade_request?` +
  //             new URLSearchParams({
  //               submission_id: SubmissionId,
  //             })
  //         );
  //         const request = await response.json();
  //         if (request.justification) {
  //           if (request.reviewed === true) {
  //             SetCheckColor("green");
  //           }
  //           if (userInfo.isStudent) {
  //             setJustification(request.justification);
  //           } else {
  //             setJustification(request.justification);
  //             if (request.reviewed === false) {
  //               setHighlight(true);
  //               setTimeout(() => setHighlight(false), 3000);
  //               message.info("Regrade Request");
  //             }
  //           }
  //         } else {
  //           setJustification("");
  //         }
  //       } catch (error) {
  //         console.log(error);
  //       } finally {
  //         setIsLoading(false); // Set loading to false after fetching
  //       }
  //     } else {
  //       setIsLoading(false); // Set loading to false if no SubmissionId
  //     }
  //   };
  //   fetchJustificationDetails();
  // }, [SubmissionId, userInfo]);

  const handleStudentClick = () => {
    setRequestModalVisible(true);
  };
  const handleInstructorClick = () => {
    setEditGradeModalVisible(true);
  };
  const handleRequestSubmission = async () => {
    if (TempJustification.trim() === "") {
      message.error("Justification can't be blank");
      return;
    }
    setRequestModalVisible(false);
    try {
      console.log(TempJustification)
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/send_regrade_request`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            submission_id: submissionId,
            justification: TempJustification,
          }),
        }
      );

      if (response.ok) {
        message.success("Request Sent");
        setRequestModalVisible(false);
        setJustification(TempJustification);
        console.log(Justification);
      } else {
        message.error("Failed to send regrade request");
      }
    } catch (error) {
      console.error("Error:", error);
      message.error("An error occurred while sending regrade request");
    }
  };
  const handleGradeSubmission = async () => {
    if (Grade.trim() === "" || isNaN(Grade)) {
      message.error("Grade can't be blank");
      return;
    }
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/update_grade`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            submission_id: submissionId,
            new_grade: parseFloat(Grade), // Ensure the grade is a float
          }),
        }
      );
      const response2 = await fetch(
        `${process.env.REACT_APP_API_URL}/set_reviewed`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            submission_id: submissionId,
          }),
        }
      );

      if (response.ok && response2.ok) {
        SetCheckColor("green");
        message.success("Grade Updated");
        setEditGradeModalVisible(false);
        console.log(`Grade updated to ${Grade}`);
      } else {
        message.error("Failed to update grade");
      }
    } catch (error) {
      console.error("Error:", error);
      message.error("An error occurred while updating grade");
    }
  };

  const justificationStyle = highlight
    ? {
        border: "5px solid #4287f5",
        padding: "10px",
        transition: "border-color 0.5s ease-out",
      }
    : {};

  if (isLoading) {
    return <p>Loading...</p>; // Render loading state
  }

  return (
    <Space
      direction="vertical"
      size="middle"
      style={{ paddingLeft: "20px", paddingTop: "20px" }}
    >
        <Space direction="horizontal" size="middle" style={{ justifyContent: "space-between", width: "100%" }}>
          <Typography.Title level={4}>{assignmentName}</Typography.Title>
          <div>
            <strong>Score Received</strong>
            <br />
            {score}
          </div>
          <div>
            <strong>Status</strong>
            <br />
            {active ? (
              <div style={{ color: 'green', border: '1px solid green', padding: '5px', display: 'inline-block' }}>
                Active
              </div>
            ) : (
              <div style={{ color: 'red', border: '1px solid red', padding: '5px', display: 'inline-block' }}>
                Not Active
              </div>
            )}
          </div>
        </Space>
      {/* <Typography.Title level={4}>{assignmentName}</Typography.Title> */}
      <Space direction="horizontal" size="middle">
        <CheckCircleOutlined style={{ color: "green" }} />
        Graded
      </Space>
      {/* only render regrade request info if this submission is active */}
      {active && <Space>
        {/* displaying the correct button if the user is a student or an instructor */}
        <Space direction="vertical" size="middle">
        {(userInfo.isStudent && Justification == "" &&(
            <Button type="primary" onClick={handleStudentClick}>
              Submit a Regrade Request
            </Button>
          )) ||
            (!userInfo.isStudent && (
              <Button type="primary" onClick={handleInstructorClick}>
                Edit Grade
              </Button>
            ))}
          {Justification && (
            <div
              ref={justificationRef}
              tabIndex={-1}
              style={justificationStyle}
            >
              <strong>Regrade Justification</strong>
              {/* conditionally render the color of this checkmark as gray or green based on if this regrade request is reviewed */}
              <CheckCircleOutlined style={{ color: CheckColor, marginLeft: 5 }} />
              <br></br>
              {Justification || "bleh"}
            </div>
          )}
        </Space>
        <Modal
          title="Regrade Request"
          open={RequestModalVisible}
          onCancel={() => setRequestModalVisible(false)}
          onOk={() => handleRequestSubmission()}
        >
          <Input.TextArea
            rows={4}
            placeholder="Enter Justification for Regrade Request"
            onChange={(e) => setTempJustification(e.target.value)}
            //onChange={(e) => setJustification(e.target.value)}
          />
        </Modal>
        <Modal
          title="Edit Grades"
          open={EditGradeModalVisible}
          onCancel={() => setEditGradeModalVisible(false)}
          onOk={() => handleGradeSubmission()}
        >
          <Input
            type="number"
            placeholder="Enter New Grade"
            onChange={(e) => setGrade(e.target.value)}
          />
        </Modal>
      </Space>}
      <Space direction="vertical" size="middle" style={{ paddingTop: "20px" }}>
        <div>Select each question to review feedback and grading details.</div>
        <div>
          <strong>Student</strong>
          <br />
          {studentName}
        </div>
        <div>
          <strong>Total Points</strong>
          <br />
          {totalPoints}
        </div>
        {/* <div>
          <strong>Score Received</strong>
          <br />
          {score}
        </div> */}
      </Space>
    </Space>
  );
}