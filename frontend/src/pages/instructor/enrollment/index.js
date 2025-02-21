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
import { useCallback, useState, useContext } from "react";
import {
  getUserByEmail,
  createEnrollment,
  createEnrollmentCSV,
  getCourseEnrollment,
} from "../../../services/enrollment";
import { useParams } from "react-router-dom";
import { useEffect } from "react";
import AddMoreUsersModal from "./AddMoreUsersModal";
import { GlobalContext } from "../../../App";
import AddCSVModal from "./AddCSVModal";
const columns = [
  { title: "NAME", dataIndex: "name" },
  { title: "EMAIL", dataIndex: "email_address" },
];

export default () => {
  const { userInfo } = useContext(GlobalContext);
  
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [addCSVModalOpen, setAddCSVModalOpen] = useState(false);
  const [addMoreUsersModalOpen, setAddMoreUsersModalOpen] = useState(false);
  const [enrollment, setEnrollment] = useState([]);
  const urlParams = useParams();
  const { courseInfo, updateCourseInfo } = useContext(GlobalContext);
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

  const getEnrollment = useCallback(() => {
    getCourseEnrollment({ course_id: courseId }).then((res) => {
      setEnrollment(res.data);
    });
  }, [courseId]);

  const handleRoleChange = useCallback(
    (newRole, studentId) => {
      message.info("You are changing a student's role in the course.");

      fetch(process.env.REACT_APP_API_URL + "/update_role", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          student_id: studentId,
          course_id: courseId,
          new_role: newRole,
        }),
      })
        .then((res) => {
          if (!res.ok) {
            return res.json().then((error) => {
              throw new Error(error.error || "Something went wrong");
            });
          }
          return res.json();
        })
        .then(() => {
          getEnrollment(); // Refresh the enrollment list
        })
        .catch((error) => {
          console.error("Error updating role:", error);
        });
    },
    [courseId, getEnrollment]
  );

  const finishForm = useCallback(
    (values) => {
      const { email } = values;
      
      getUserByEmail({ email: email })
        .then((res) => {
          createEnrollment({
            student_id: res.data.id,
            course_id: courseId,
            role: values.role, // Include the role from form values
          })
            .then(() => {
              toggleAddModalOpen();
              getEnrollment();
            })
            .catch((error) => {
              console.error("Error creating enrollment:", error);
            });
      })
      .catch((error) => {
        console.error("Error fetching user:", error);
      });
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

      function enrollEntry(item) {
        fetch(
          process.env.REACT_APP_API_URL + "/get_users?" +
            new URLSearchParams({
              email: item,
            })
        )
          .then((res) => res.json())
          .then((student) =>
            createEnrollment({
              'student_id': student.id,
              'course_id': courseId,
            }).then(() => {
              toggleAddMoreUsersModalOpen();
              getEnrollment();
            })
          );
      }
    },
    [courseId, getEnrollment, toggleAddMoreUsersModalOpen]
  );

  useEffect(() => {
    getEnrollment();
  }, [getEnrollment]);

  return (
    <>
      <PageHeader
        title="Course Roster"
        style={{ borderBottom: "1px solid #f0f0f0" }}
      />
      <Card bordered={false}>
        <Form layout="inline" style={{ marginBottom: "20px" }}>
          <Form.Item name="role">
            <Select
              placeholder="view by role"
              style={{ width: "180px" }}
              options={[
                { label: "All", value: "0" },
                { label: "Students", value: "1" },
                { label: "Instructors", value: "2" },
                { label: "TAs", value: "3" },
                { label: "Readers", value: "4" },
              ]}
            />
          </Form.Item>
          <Form.Item name="section">
            <Input placeholder="view by section" />
          </Form.Item>
          <Form.Item name="username">
            <Input placeholder="view by name" />
          </Form.Item>
          <Form.Item>
            <Button type="primary">search</Button>
          </Form.Item>
        </Form>
        <Table
          columns={[
            ...columns,
            {
              title: "ROLE",
              dataIndex: "role",
              render: (text, record) => (
                <Select
                  defaultValue={text}
                  style={{ width: 120 }}
                  onChange={(value) => handleRoleChange(value, record.id)}
                  disabled={text === "instructor"} // Disable dropdown if the role is instructor
                >
                  <Select.Option value="student">Student</Select.Option>
                  <Select.Option value="TA">TA</Select.Option>
                  <Select.Option value="instructor">Instructor</Select.Option>
                </Select>
              ),
            },
          ]}
          dataSource={enrollment}
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
