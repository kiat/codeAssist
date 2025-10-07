import {
  Button,
  Card,
  Form,
  Input,
  PageHeader,
  Select,
  Space,
  Table,
  Typography,
  message
} from "antd";
import { PlusOutlined } from "@ant-design/icons";
import AddUserModal from "./AddUserModal";
import { useCallback, useState, useEffect } from "react";
import {
  createEnrollment,
  createEnrollmentCSV,
  getCourseEnrollment,
  updateRole
} from "../../../services/course";
import {
  getUserByEmail,
} from "../../../services/user";
import { useParams } from "react-router-dom";
import AddMoreUsersModal from "./AddMoreUsersModal";
import AddCSVModal from "./AddCSVModal";
const columns = [
  {
    title: "NAME",
    dataIndex: "name",
    sorter: (a, b) => (a.name || "").localeCompare(b.name || ""),
    sortDirections: ["ascend", "descend"],
  },
  {
    title: "EMAIL",
    dataIndex: "email_address",
    sorter: (a, b) =>
      (a.email_address || "").localeCompare(b.email_address || ""),
    sortDirections: ["ascend", "descend"],
  },
];

export default () => {
  const [form] = Form.useForm();
  
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [addCSVModalOpen, setAddCSVModalOpen] = useState(false);
  const [addMoreUsersModalOpen, setAddMoreUsersModalOpen] = useState(false);
  const [enrollment, setEnrollment] = useState([]);
  const [filteredEnrollment, setFilteredEnrollment] = useState([]);
  const urlParams = useParams();
  const { courseId } = urlParams;

  const toggleAddModalOpen = useCallback(() => {
    setAddModalOpen((t) => !t);
  }, []);
  
  const toggleAddCSVModalOpen = useCallback(() => {
    setAddCSVModalOpen((t) => !t);
  }, []);

  const toggleAddMoreUsersModalOpen = useCallback(() => {
    setAddMoreUsersModalOpen((t) => !t);
  }, []);

  const applyFilters = useCallback((data, filters = {}) => {
    const { role, section, username } = filters;
    const normalizedRole = role ? role.toLowerCase() : null;
    const normalizedSection = section ? section.toLowerCase() : null;
    const normalizedUsername = username ? username.toLowerCase() : null;

    return data.filter((entry) => {
      const entryRole = (entry.role || "").toLowerCase();
      const entrySection = (entry.section || "").toLowerCase();
      const entryName = (entry.name || "").toLowerCase();
      const entryEmail = (entry.email_address || "").toLowerCase();

      const matchesRole = !normalizedRole || entryRole === normalizedRole;
      const matchesSection =
        !normalizedSection || entrySection.includes(normalizedSection);
      const matchesUsername =
        !normalizedUsername ||
        entryName.includes(normalizedUsername) ||
        entryEmail.includes(normalizedUsername);

      return matchesRole && matchesSection && matchesUsername;
    });
  }, []);

  const getEnrollment = useCallback(() => {
    getCourseEnrollment({ course_id: courseId }).then((res) => {
      const data = res.data || [];
      setEnrollment(data);
      const currentFilters = form.getFieldsValue(true);
      setFilteredEnrollment(applyFilters(data, currentFilters));
    });
  }, [courseId, applyFilters, form]);

  const handleUpdateRole = useCallback(
    async (newRole, studentId) => {
      try {
        await updateRole({
          "student_id": studentId,
          "course_id": courseId,
          "new_role": newRole
        });
        message.info("User role updated")
        getEnrollment();
      }
      catch(error) {
        console.error("Error updating role: ", error);
      }
    },
    [courseId, getEnrollment]
  );

  const finishForm =  useCallback(
    async (values) => {
      const { email } = values;

      try {
        const res = await getUserByEmail({ email: email });
        await createEnrollment({
          student_id: res.data.id,
          course_id: courseId,
          role: values.role,
        });
        message.success("Successfully created enrollment")
        toggleAddModalOpen();
        getEnrollment();
      }
      catch(error) {
        console.error("Error creating enrollments: ", error);
      }
    }, [courseId, getEnrollment, toggleAddModalOpen]
  );
  
  const finishCSVForm = useCallback(
    async (formData) => {
      formData.append("course_id", courseId);

      return createEnrollmentCSV(formData)
        .then((res) => {
          if (res.status !== 200) {
            return res.data.then((error) => {
              throw new Error(error.error || "Something went wrong");
            });
          }
          return res.data;
        })
  }, [courseId]);
  
  const finishMoreUsers = useCallback(
    (values) => {
      console.log(values);
      values.forEach(enrollEntry);

      async function enrollEntry(item) {
        try {
          const res = await getUserByEmail({ email: item });
          await createEnrollment({
            student_id: res.data.id,
            course_id: courseId,
            role: values.role,
          });
          message.success("Successfully created enrollment")
          getEnrollment();
        }
        catch(error) {
          console.error("Error creating enrollments: ", error);
        }
      }
      toggleAddMoreUsersModalOpen();
    },
    [courseId, getEnrollment, toggleAddMoreUsersModalOpen]
  );

  useEffect(() => {
    getEnrollment();
  }, [getEnrollment]);

  const handleFormValuesChange = useCallback(
    (_, allValues) => {
      setFilteredEnrollment(applyFilters(enrollment, allValues));
    },
    [applyFilters, enrollment]
  );

  const handleFormFinish = useCallback(
    (values) => {
      setFilteredEnrollment(applyFilters(enrollment, values));
    },
    [applyFilters, enrollment]
  );

  const tableColumns = [
    ...columns,
    {
      title: "ROLE",
      dataIndex: "role",
      sorter: (a, b) => (a.role || "").localeCompare(b.role || ""),
      sortDirections: ["ascend", "descend"],
      filters: [
        { text: "Instructors", value: "instructor" },
        { text: "Students", value: "student" },
        { text: "TAs", value: "ta" },
        { text: "Readers", value: "reader" },
      ],
      onFilter: (value, record) =>
        (record.role || "").toLowerCase() === value,
      render: (_, record) => (
        <Select
          value={record.role}
          style={{ width: 140 }}
          onChange={(value) => handleUpdateRole(value, record.id)}
          disabled={(record.role || "").toLowerCase() === "instructor"}
        >
          <Select.Option value="student">Student</Select.Option>
          <Select.Option value="TA">TA</Select.Option>
          <Select.Option value="instructor">Instructor</Select.Option>
          <Select.Option value="reader">Reader</Select.Option>
        </Select>
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Course Roster"
        style={{ borderBottom: "1px solid #f0f0f0" }}
      />
      <Card bordered={false}>
        <Form
          form={form}
          layout="inline"
          style={{ marginBottom: "20px" }}
          onValuesChange={handleFormValuesChange}
          onFinish={handleFormFinish}
        >
          <Form.Item name="role">
            <Select
              placeholder="view by role"
              style={{ width: "180px" }}
              allowClear
              options={[
                { label: "Instructors", value: "instructor" },
                { label: "Students", value: "student" },
                { label: "TAs", value: "TA" },
                { label: "Readers", value: "reader" },
              ]}
            />
          </Form.Item>
          <Form.Item name="section">
            <Input placeholder="view by section" allowClear />
          </Form.Item>
          <Form.Item name="username">
            <Input placeholder="view by name or email" allowClear />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">
              search
            </Button>
          </Form.Item>
        </Form>
        <Table
          columns={tableColumns}
          dataSource={filteredEnrollment}
          rowKey="id"
        />
      </Card>
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
        <Space size="large">
          <Typography.Title level={5}>50 students</Typography.Title>
          <Typography.Title level={5}>2 instructors</Typography.Title>
          <Typography.Title level={5}>2 TAs</Typography.Title>
        </Space>
        <div
          style={{
            float: "right",
            marginRight: "225px",
          }}
        >
          <Space>
            {/* <Button icon={<UploadOutlined />}>Download Enrollment</Button> */}
            <Button icon={<PlusOutlined />} onClick={toggleAddModalOpen}>
              Add Students or Staff
            </Button>
            <Button icon={<PlusOutlined />} onClick={toggleAddCSVModalOpen}>
              Add With CSV
            </Button>
            <Button
              icon={<PlusOutlined />}
              onClick={toggleAddMoreUsersModalOpen}
            >
              Add More Students
            </Button>
          </Space>
        </div>
      </div>
      <AddUserModal
        open={addModalOpen}
        toggleAddModalOpen={toggleAddModalOpen}
        onFinish={finishForm}
      />
      <AddCSVModal 
        open={addCSVModalOpen} 
        toggleAddCSVModalOpen={toggleAddCSVModalOpen} 
        finishCSVForm={finishCSVForm} 
        getEnrollment={getEnrollment}
      />
      <AddMoreUsersModal
        toggleAddMoreUsersModalOpen={toggleAddMoreUsersModalOpen}
        open={addMoreUsersModalOpen}
        finishMoreUsers={finishMoreUsers}
      />
    </>
  );
};
