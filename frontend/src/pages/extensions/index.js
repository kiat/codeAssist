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
import { CloseOutlined } from "@ant-design/icons";
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
  const [extensions, setExtensions] = useState([]);
  const [forceUpdate, setForceUpdate] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
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
      message.success("Extension created successfully");
      toggleExtensionModalOpen();
      setForceUpdate((u) => u + 1);
    })
    .catch((err) => {
      console.error("Failed to create extension", err);
      message.error("Failed to create extension. Please try again.");
    });
};

  const deleteExtension = async (record) => {
    console.log("ID", record.id);
    const response = await fetch(
      `${process.env.REACT_APP_API_URL}/delete_extension?extension_id=${record.id}`,
      { method: "DELETE" }
    );
    if (response.ok) {
      setForceUpdate((u) => u + 1);
      message.success("Extension deleted successfully");
    } else {
      message.error("Failed to delete extension");
    }
  };

  useEffect(() => {
    const fetchAssignmentExtensions = async () => {
      try {
        const extensionsResponse = await fetch(
          `${process.env.REACT_APP_API_URL}/get_assignment_extensions?assignment_id=${assignmentId}`
        );
        const extensionsData = await extensionsResponse.json();
        const updatedExtensions = await Promise.all(
          extensionsData.map(async (extension) => {
            try {
              const student = await fetch(
                `${process.env.REACT_APP_API_URL}/get_user_by_id?id=${extension.student_id}`
              );
              const studentData = await student.json();
              return {
                ...extension,
                name: studentData.name,
              };
            } catch (error) {
              console.error("Error fetching extension data:", error);
            }
          })
        );
        setExtensions(updatedExtensions);
      } catch (error) {
        message.error("Failed to fetch extensions.");
        console.error("Error fetching extensions:", error);
      }
    };
    fetchAssignmentExtensions();
    const fetchCourseStudents = async () => {
      try {
        const studentsResponse = await fetch(
          `${process.env.REACT_APP_API_URL}/get_course_enrollment?course_id=${courseInfo.id}`
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
  }, [courseInfo.id, forceUpdate]);
  const [extensionModalOpen, setExtensionModalOpen] = useState(false);

  const toggleExtensionModalOpen = useCallback(() => {
    setExtensionModalOpen((t) => !t);
  }, []);

  const columns = [
    {
      title: "NAME",
      dataIndex: "name",
      key: "name",
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (text) => text,
    },
    {
      title: "RELEASE (CST)",
      dataIndex: "release_date_extension",
      key: "release_date_extension",
      render: (text) => {
        const dateToDisplay = text || assignmentInfo?.published_date;
        return dateToDisplay
          ? moment(dateToDisplay).format("MMM DD [AT] h:mmA").toUpperCase()
          : "--";
      },
      sorter: (a, b) =>
        moment(a.published_date).unix() - moment(b.published_date).unix(),
    },
    {
      title: "DUE (CDT)",
      dataIndex: "due_date_extension",
      key: "due_date_extension",
      render: (text) => {
        const dateToDisplay = text || assignmentInfo?.due_date;
        return dateToDisplay
          ? moment(dateToDisplay).format("MMM DD [AT] h:mmA").toUpperCase()
          : "--";
      },
      sorter: (a, b) => moment(a.due_date).unix() - moment(b.due_date).unix(),
    },
    {
      title: "LATE DUE (CDT)",
      dataIndex: "late_due_date_extension",
      key: "late_due_date_extension",
      render: (text) => {
        const dateToDisplay = text || assignmentInfo?.late_due_date;
        return dateToDisplay
          ? moment(dateToDisplay).format("MMM DD [AT] h:mmA").toUpperCase()
          : "--";
      },
      sorter: (a, b) => moment(a.due_date).unix() - moment(b.due_date).unix(),
    },
    {
      title: "EDIT",
      align: "center",
      render: (_, record) => (
        <Button
          danger
          type="primary"
          size="small"
          icon={<CloseOutlined />}
          onClick={() => deleteExtension(record)}
        />
      ),
    },
  ];

  const filteredExtensions = extensions.filter((extension) =>
    extension.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
              onSearch={(value) => setSearchQuery(value)}
            />
            <Table
              rowKey="id"
              columns={columns}
              dataSource={filteredExtensions}
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
