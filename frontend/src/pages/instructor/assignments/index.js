// import { Tabs } from "antd";
import { CopyFilled, DownloadOutlined } from "@ant-design/icons";
import { Button, Form, PageHeader, Popover, Space, Typography } from "antd";
import { useCallback, useState } from "react";
import { useParams } from "react-router-dom";
import { createAssignment } from "../../../services/course";
import Assignments from "./Assignments";
import CreateAssignment from "./CreateAssignment";
import DuplicateAssignmentModal from "./DuplicateAssignmentModal";

export default function InstructorAssignments() {
  const [isCreate, setIsCreate] = useState(false);
  const [isDuplicateAssignmentModalOpen, setIsDuplicateAssignmentModalOpen] =
    useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [form] = Form.useForm();
  const { courseId } = useParams();

  const updateCurrentStep = useCallback(current => {
    setCurrentStep(current);
  }, []);

  const toggleDuplicateAssignmentModal = useCallback(() => {
    setIsDuplicateAssignmentModalOpen(b => !b);
  }, []);

  const toggleIsCreate = useCallback(() => {
    setIsCreate(t => !t);
  }, []);

  const finishForm = () => {
    const values = form.getFieldsValue();
    const assignmentData = {
      name: values.name, 
      course_id: courseId, 
      due_date: values.dueDate._d, 
      autograder_points: values.autograderPoints, 
      anonymous_grading: values.submissionAnonymization,
      manual_grading: values.manualGrading,
      late_submission: values.allowLateSubmissions,
      late_due_date: values.lateDueDate,
      enable_group: values.groupSubmission,
      group_size: values.limitGroupSize,
      leaderboard: values.leaderBoard,
      published_date: values.releaseDate._d,
    };
    const validData = Object.fromEntries(
      Object.entries(assignmentData).filter(([_, value]) => value !== undefined)
    );
    createAssignment(validData).then(res => {
      toggleIsCreate();
    });
   
  
  };

  return (
    <>
      <div
        style={{
          height: "calc(100vh - 40px)",
          overflow: "auto",
        }}
      >
        {/* <PageHeader title={isCreate ? "Create Assignment" : "38 Assignments"} /> */}
        <div style={{ display: isCreate ? "none" : "inline" }}>
          {/* <Assignments toggleIsCreate={toggleIsCreate} /> */}
          <Assignments isCreate={isCreate} />
        </div>
        <div style={{ display: isCreate ? "inline" : "none" }}>
          <CreateAssignment
            currentStep={currentStep}
            updateCurrentStep={updateCurrentStep}
            toggleIsCreate={toggleIsCreate}
            form={form}
          />
        </div>
      </div>
      <div
        style={{
          backgroundColor: "#1890ff",
          position: "fixed",
          width: "100%",
          bottom: 0,
          lineHeight: "40px",
          color: "white",
          fontWeight: "bold",
          marginLeft: "-1px",
        }}
      >
        <div
          style={{
            float: "right",
            marginRight: "225px",
          }}
        >
          {isCreate ? (
            currentStep === 1 ? (
              <Button onClick={finishForm}>Save Assignment</Button>
            ) : (
              <div style={{ height: "40px" }} />
            )
          ) : (
            <Space>
              <Popover
                content={
                  <Space direction='vertical' style={{ color: "black" }}>
                    <Typography.Link>
                      <DownloadOutlined />
                      <span> Download CSV</span>
                    </Typography.Link>
                    <Typography.Link>
                      <DownloadOutlined />
                      <span> Download for Excel</span>
                    </Typography.Link>
                  </Space>
                }
              >
                <Button icon={<DownloadOutlined />}>Download Grades</Button>
              </Popover>
              <Button
                onClick={toggleDuplicateAssignmentModal}
                icon={<CopyFilled />}
              >
                Duplicate Assignment
              </Button>
              <Button onClick={toggleIsCreate}>Create Assignment</Button>
            </Space>
          )}
        </div>
      </div>
      <DuplicateAssignmentModal
        open={isDuplicateAssignmentModalOpen}
        toggleCreateAssignmentModal={toggleDuplicateAssignmentModal}
      />
    </>
  );
}