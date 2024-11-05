import { PlusOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Form,
  Input,
  message,
  PageHeader,
  Space,
  Table,
  Typography,
} from "antd";
import { useCallback } from "react";
import { useState, useEffect, useContext } from "react";
import { useParams } from "react-router-dom";
import { GlobalContext } from "../../App";
import { createExtension } from "../../services/assignment";
import PageBottom from "../../components/layout/pageBottom";
import PageContent from "../../components/layout/pageContent";
import ExtensionModal from "./ExtensionModal";
import moment from "moment";

export default () => {
  const { assignmentId } = useParams();
  const [form] = Form.useForm();
  const [courseStudents, setCourseStudents] = useState([]);
  const [assignmentInfo, setAssignmentInfo] = useState(null);
  const { courseInfo } = useContext(GlobalContext);
  const finishForm = async () => {
    const values = form.getFieldsValue();
    const extensionData = {
      assignment_id: assignmentId,
      student_id: values.student,
      release_date_extension: values.releaseDate || null,
      due_date_extension: values.dueDate || null,
      late_due_date_extension: values.lateDueDate || null,
    };
    createExtension(extensionData)
      .then((res) => {
        toggleExtensionModalOpen();
      })
      .catch((err) => {
        if (!values.student) {
          message.error("Select a student");
        } else {
          message.error("Failed to create extension");
        }
      });
  };
  useEffect(() => {
    const fetchCourseStudents = async () => {
      try {
        const studentsResponse = await fetch(
          `${process.env.REACT_APP_API_URL}/get_student_enrollment?course_id=${courseInfo.id}`
        );
        const studentsData = await studentsResponse.json();
        setCourseStudents(studentsData);
      } catch (error) {
        message.error("Failed to fetch course students.");
        console.error("Error fetching students:", error);
      }
    };
    fetchCourseStudents();
    const fetchAssignmentDetails = async () => {
      try {
        const assignmentResponse = await fetch(
          `${process.env.REACT_APP_API_URL}/get_assignment?assignment_id=${assignmentId}`
        );
        const assignmentData = await assignmentResponse.json();
        setAssignmentInfo(assignmentData);
      } catch (error) {
        message.error("Failed to fetch assignment details.");
        console.error("Error fetching assignment details:", error);
      }
    };
    fetchAssignmentDetails();
  }, [courseInfo.id]);
  const [extensionModalOpen, setExtensionModalOpen] = useState(false);

  const toggleExtensionModalOpen = useCallback(() => {
    setExtensionModalOpen((t) => !t);
  }, []);

  const columns = [
    { title: "FIRST & LAST NAME", dataIndex: "" },
    { title: "EXTENSION TYPE", dataIndex: "" },
    { title: "RELEASE (CST)", dataIndex: "" },
    { title: "DUE (CST)", dataIndex: "" },
    { title: "LATE DUE (CST)", dataIndex: "" },
    { title: "EDIT", dataIndex: "" },
  ];
  return (
    <>
      <PageContent>
        <PageHeader title="Extensions" />
        <Card title="Assignsment Settings" bordered={false}>
          <Space size="large">
            <div>
              <Typography.Title level={5}>RELEASE DATE (CST)</Typography.Title>
              <p>
                {assignmentInfo && assignmentInfo.published_date
                  ? moment(assignmentInfo.published_date).format(
                      "yyyy-MM-DD HH:mm:ss"
                    )
                  : "--"}
              </p>
            </div>
            <div>
              <Typography.Title level={5}>DUE DATE (CST)</Typography.Title>
              <p>
                {assignmentInfo && assignmentInfo.due_date
                  ? moment(assignmentInfo.due_date).format(
                      "yyyy-MM-DD HH:mm:ss"
                    )
                  : "--"}
              </p>
            </div>
            <div>
              <Typography.Title level={5}>LATE DATE (CST)</Typography.Title>
              <p>
                {assignmentInfo && assignmentInfo.late_due_date
                  ? moment(assignmentInfo.late_due_date).format(
                      "yyyy-MM-DD HH:mm:ss"
                    )
                  : "--"}
              </p>
            </div>
          </Space>
        </Card>
        <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
          <Space direction="vertical" style={{ width: "100%" }}>
            <Input.Search
              enterButton
              placeholder="Find a student"
              style={{ width: "300px" }}
            />
            <Table
              rowKey="id"
              columns={columns}
              dataSource={[]}
              locale={{
                emptyText: (
                  <div style={{ marginTop: "50px", marginBottom: "50px" }}>
                    <Typography.Title level={4}>
                      There are no assignment extensions.
                    </Typography.Title>
                    <Typography.Paragraph>
                      Add an extension for a student below.
                    </Typography.Paragraph>
                    <Button
                      type="primary"
                      ghost
                      shape="round"
                      onClick={toggleExtensionModalOpen}
                    >
                      Add an Extension
                    </Button>
                  </div>
                ),
              }}
            />
          </Space>
        </Card>
      </PageContent>
      <PageBottom>
        <Button onClick={toggleExtensionModalOpen}>
          <span>Add an Extension</span>
          <PlusOutlined />
        </Button>
      </PageBottom>
      <ExtensionModal
        open={extensionModalOpen}
        onCancel={toggleExtensionModalOpen}
        students={courseStudents}
        assignmentInfo={assignmentInfo}
        onFinish={finishForm}
        form={form}
      />
    </>
  );
};
