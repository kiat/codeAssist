  import React, { useContext, useCallback, useEffect, useState } from "react";
  import { useParams, useLocation } from "react-router-dom";
  import { Card, PageHeader, Radio } from "antd";


  import { GlobalContext } from "../../App";
  import PageContent from "../../components/layout/pageContent";
  import PageBottom from "../../components/layout/pageBottom";
  import TestResultsDisplay from "./TestResultsDisplay";
  import ActionButtons from "./ActionButtons";


  import UploadModal from "../../components/UploadModal";
  import SubmissionHistoryModal from "./submissionHistoryModal";
  import FormattingModal from "./FormattingModal";


  import { getAssignment } from "../../services/assignment";


  export default function AssignmentResult() {
    const [viewMode, setViewMode] = useState("Results");
    const [uploadModalOpen, setUploadModalOpen] = useState(false);
    const [historyModalOpen, setHistoryModalOpen] = useState(false);
    const [formattingModalOpen, setFormattingOpen] = useState(false);
    const [autoGraderPoints, setAutograderPoints] = useState(0);
    const [assignmentName, setAssignmentName] = useState(""); // Placeholder value
    const { assignmentId, studentId } = useParams();
    const location = useLocation();
    //adding global context variable
    const { userInfo, assignmentInfo, updateAssignmentInfo } = useContext(GlobalContext);
  //updating useEffect dependencies, adding functionalit to render the students name ase don their id
  useEffect(() => {
    const fetchAssignmentDetails = async () => {
      const res = await getAssignment({ assignment_id: assignmentId });
      if (res?.data) {
        setAutograderPoints(res.data.autograder_points);
        setAssignmentName(res.data.name); // Assuming the API provides this
        updateAssignmentInfo((prevInfo) => ({
          ...prevInfo,
          name: res.data.name,
          id: assignmentId,
        }));
      }
    };

    const fetchStudentName = async () => {
      if (studentId) {
        try {
          const response = await fetch(
            `${process.env.REACT_APP_API_URL}/get_student_by_id?` +
            new URLSearchParams({
              id: studentId,
            })
          );
          const studentData = await response.json();
          if (studentData) {
            updateAssignmentInfo((prevInfo) => ({
              ...prevInfo,
              studentName: studentData.name,
              studentId: studentId,
            }));
          }
        } catch (error) {
          console.error("Failed to fetch student data:", error);
        }
      }
    };

    fetchAssignmentDetails();
    fetchStudentName();
  }, [assignmentId, studentId, location.key, updateAssignmentInfo]);


    const toggleModal = useCallback((type) => {
      if (type === 'upload') setUploadModalOpen(prev => !prev);
      else if (type === 'history') setHistoryModalOpen(prev => !prev);
      else if (type === 'formatting') setFormattingOpen(prev => !prev);
    }, []);


    const handleRadioChange = useCallback((e) => {
      setViewMode(e.target.value);
    }, []);


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
                  </Radio.Group>
                ]}
              />
              <Card bordered={false}>
              <TestResultsDisplay viewMode={viewMode} studentId={studentId} assignmentName={assignmentName}
              studentName={assignmentInfo?.studentName ?? userInfo?.name}
              score={assignmentInfo?.score ?? "Unknown"} // Replace with actual score data as needed
              totalPoints={autoGraderPoints}/>
              </Card>
            </div>
          </div>
        </PageContent>
        <PageBottom>
          <ActionButtons
            onRerun={() => {}} // Implement or replace with actual function
            onUpload={() => toggleModal('upload')}
            onDownload={() => {}} // Implement or replace with actual function
            onHistoryOpen={() => toggleModal('history')}
            isStudent={userInfo?.isStudent}
          />
        </PageBottom>
        <UploadModal open={uploadModalOpen} onCancel={() => toggleModal('upload')} />
        <SubmissionHistoryModal
          open={historyModalOpen}
          onCancel={() => toggleModal('history')}
          studentId={userInfo?.id}
          assignmentId={assignmentId}
          studentName={userInfo?.name}/>
        <FormattingModal open={formattingModalOpen} onCancel={() => toggleModal('formatting')} />
      </>
    );
  }
