import React, { useContext, useCallback, useEffect, useState } from "react";
import { useParams, useLocation } from "react-router-dom";
import { Card, PageHeader, Radio, message } from "antd";

import { GlobalContext } from "../../App";
import PageContent from "../../components/layout/pageContent";
import PageBottom from "../../components/layout/pageBottom";
import TestResultsDisplay from "./TestResultsDisplay";
import ActionButtons from "./ActionButtons";

import UploadModal from "../../components/UploadModal";
import SubmissionHistoryModal from "./submissionHistoryModal";
import FormattingModal from "./FormattingModal";

import { getAssignment, getExtension } from "../../services/assignment";
import moment from "moment";

export default function AssignmentResult() {
  const [viewMode, setViewMode] = useState("Results");
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  const [formattingModalOpen, setFormattingOpen] = useState(false);
  const [autoGraderPoints, setAutograderPoints] = useState(0);
  const [assignmentName, setAssignmentName] = useState(""); // Placeholder value
  //chnaging the whole file to use the submisison id in the params instead of teh assingment id and submission id passed in
  const { submissionId } = useParams();
  const [assignmentId, setAssignmentId] = useState("");
  const [studentId, setStudentId] = useState("");
  //const { assignmentId, studentId } = useParams();
  const location = useLocation();
  //adding global context variable
  const { userInfo, assignmentInfo, updateAssignmentInfo } =
    useContext(GlobalContext);
  const [toSend, setToSend] = useState();
  const [dueDate, setDueDate] = useState();
  const [lateDueDate, setLateDueDate] = useState();
  const [lateAllowed, setLateAllowed] = useState();
  
  useEffect(() => {
    // Fetching student and assignment IDs based on this submission ID
    const fetchIds = async () => {
      console.log("Fetching IDs based on submission ID:", submissionId);
      try {
        const details = await fetch(
          `${process.env.REACT_APP_API_URL}/get_submission_details?submission_id=${submissionId}`
        );
        const data = await details.json();
        if (data) {
          setToSend(data);
          console.log("Fetched IDs:", data.assignment_id, data.student_id);
          setAssignmentId(data.assignment_id);
          setStudentId(data.student_id);
        } else {
          console.log("No response data");
        }
      } catch (error) {
        console.error("Failed to fetch IDs:", error);
      }
    };
    fetchIds();
  }, [submissionId]);

  useEffect(() => {
    if (!assignmentId || !studentId) {
      console.log(
        "Assignment ID or Student ID not yet set:",
        assignmentId,
        studentId
      );
      return;
    }

    const fetchAssignmentDetails = async () => {
      try {
        const res = await getAssignment({ assignment_id: assignmentId });
        const extension = await getExtension({
          assignment_id: assignmentId,
          student_id: studentId,
        });
        if (res?.data) {
          console.log("Im in");
          setAutograderPoints(res.data.autograder_points);
          setAssignmentName(res.data.name); // Assuming the API provides this
          setDueDate(moment(res.data.due_date).valueOf());
          setLateAllowed(res.data.late_submission);
          setLateDueDate(moment(res.data.late_due_date).valueOf());
          if (extension?.data.due_date_extension) {
            setDueDate(moment(extension.data.due_date_extension).valueOf());
          }
          if (extension?.data.late_due_date_extension) {
            setDueDate(
              moment(extension.data.late_due_date_extension).valueOf()
            );
            setLateAllowed(true);
          }
          updateAssignmentInfo((prevInfo) => ({
            ...prevInfo,
            name: res.data.name,
            id: assignmentId,
          }));
        }
        console.log(assignmentId);
      } catch (error) {
        console.error("Failed to fetch assignment details:", error);
      }
    };

    const fetchStudentName = async () => {
      try {
        const response = await fetch(
          `${process.env.REACT_APP_API_URL}/get_student_by_id?id=${studentId}`
        );
        const studentData = await response.json();
        if (studentData) {
          console.log("im in");
          updateAssignmentInfo((prevInfo) => ({
            ...prevInfo,
            studentName: studentData.name,
            studentId: studentId,
          }));
        }
        console.log(studentId);
      } catch (error) {
        console.error("Failed to fetch student data:", error);
      }
    };

    fetchAssignmentDetails();
    fetchStudentName();
  }, [submissionId, assignmentId, studentId, updateAssignmentInfo]);

  const toggleModal = useCallback(
    (type) => {
      if (type === "upload") {
        //if the due date hasnt passed open the model or else send an error message saying dude date has passes
        const now = moment();
        if (!now.isAfter(dueDate)) {
          setUploadModalOpen((prev) => !prev);
        } else if (lateAllowed && !now.isAfter(lateDueDate)) {
          setUploadModalOpen((prev) => !prev);
        } else {
          message.error("Due Date Has Passed");
        }
      } else if (type === "history") setHistoryModalOpen((prev) => !prev);
      else if (type === "formatting") setFormattingOpen((prev) => !prev);
    },
    [dueDate]
  );

  const handleRadioChange = useCallback((e) => {
    setViewMode(e.target.value);
  }, []);
  const Reload = useCallback(() => {
    window.location.reload();
  }, []);

  const handleDownload = () => {
    if (toSend && toSend.student_code_file && toSend.file_name) {
      const blob = new Blob([toSend.student_code_file], { type: "text/plain" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = toSend.file_name;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } else {
      message.error("File not available for download");
    }
  };

  return (
    <>
      <PageContent>
        <div style={{ display: "flex" }}>
          <div style={{ flex: "1", height: "calc(100vh - 40px)" }}>
            <PageHeader
              style={{ borderBottom: "1px solid #f0f0f0" }}
              title={viewMode}
              extra={[
                <Radio.Group
                  key="viewMode"
                  buttonStyle="solid"
                  defaultValue="Results"
                  onChange={handleRadioChange}
                >
                  <Radio.Button value="Results">Results</Radio.Button>
                  <Radio.Button value="Code">Code</Radio.Button>
                </Radio.Group>,
              ]}
            />
            <Card bordered={false}>
              {toSend && (
                <TestResultsDisplay
                  viewMode={viewMode}
                  assignmentName={assignmentName}
                  studentName={assignmentInfo?.studentName ?? userInfo?.name}
                  score={assignmentInfo?.score ?? "Unknown"} // Replace with actual score data as needed
                  totalPoints={autoGraderPoints}
                  data={toSend}
                />
              )}
              {/* old calls */}
              {/* {studentId && assignmentId && <TestResultsDisplay viewMode={viewMode} studentId={studentId} assignmentName={assignmentName}
              //<TestResultsDisplay viewMode={viewMode} studentId={studentId} assignmentName={assignmentName}
              studentName={assignmentInfo?.studentName ?? userInfo?.name}
              score={assignmentInfo?.score ?? "Unknown"} // Replace with actual score data as needed
              totalPoints={autoGraderPoints}/>} */}
            </Card>
          </div>
        </div>
      </PageContent>
      {userInfo.isStudent ? (
        <PageBottom>
          <ActionButtons
            onRerun={() => {}} // Implement or replace with actual function
            onUpload={() => toggleModal("upload")}
            onDownload={handleDownload} // Implement or replace with actual function
            onHistoryOpen={() => toggleModal("history")}
            isStudent={userInfo?.isStudent}
          />
        </PageBottom>
      ) : (
        <></>
      )}
      {/* sending required data to upload modal */}
      <UploadModal
        open={uploadModalOpen}
        onCancel={() => toggleModal("upload")}
        assignmentID={assignmentId}
        assignmentTitle={assignmentName}
        extra={() => Reload()}
      />
      <SubmissionHistoryModal
        open={historyModalOpen}
        onCancel={() => toggleModal("history")}
        studentId={userInfo?.id}
        assignmentId={assignmentId}
        studentName={userInfo?.name}
        extra={() => Reload()}
        currSubData={toSend}
      />
      <FormattingModal
        open={formattingModalOpen}
        onCancel={() => toggleModal("formatting")}
      />
    </>
  );
}
