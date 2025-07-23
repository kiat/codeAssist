import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Typography,
  message,
  Spin,
  Space,
  Switch,
  Popconfirm,
  Table,
  Modal,
} from "antd";

const { Title } = Typography;

export default function AdminCourseManage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const [course, setCourse] = useState(null);
  const [instructors, setInstructors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [enrolledStudents, setEnrolledStudents] = useState([]);
  const [showAddStudent, setShowAddStudent] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);

        // Fetch course info
        const res = await fetch(
          `${process.env.REACT_APP_API_URL}/get_course_info?course_id=${courseId}`
        );
        const data = await res.json();
        const courseObj = data[0];
        if (!courseObj) throw new Error("Course not found");

        setCourse(courseObj);

        // Fetch instructor EID using instructor_id
        const eidRes = await fetch(
          `${process.env.REACT_APP_API_URL}/get_user_by_id?id=${courseObj.instructor_id}`
        );
        if (!eidRes.ok) throw new Error("Failed to fetch instructor EID");
        const eidData = await eidRes.json();
        const instructorEid = eidData.sis_user_id;

        // Set form fields
        form.setFieldsValue({
          ...courseObj,
          description: courseObj.description || "",
          entryCode: courseObj.entryCode || "",
          allowEntryCode: courseObj.allowEntryCode ?? true,
          instructor_eid: instructorEid, // pre-fill EID here
        });

        const instRes = await fetch(
          `${process.env.REACT_APP_API_URL}/get_all_instructors`
        );
        const instructorsData = await instRes.json();
        setInstructors(instructorsData);

        // Fetch students enrolled in this course
        const studentsRes = await fetch(
          `${process.env.REACT_APP_API_URL}/get_course_enrollment?course_id=${courseId}`
        );
        if (studentsRes.ok) {
          const studentsData = await studentsRes.json();
          setEnrolledStudents(studentsData);
        } else {
          setEnrolledStudents([]);
        }
      } catch (err) {
        console.error(err);
        message.error("Failed to load course or instructor data.");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [courseId, form]);

  const handleSave = async (values) => {
    try {
      setSaving(true);

      // Get instructor ID from EID
      const eid = values.instructor_eid;
      const res = await fetch(
        `${process.env.REACT_APP_API_URL}/get_instructor_by_eid?eid=${eid}`
      );
      if (!res.ok) throw new Error("Instructor not found");
      const instructor = await res.json();

      const payload = {
        ...values,
        course_id: courseId,
        instructor_id: instructor.id,
        description: values.description || "",
        entryCode: values.entryCode || "",
        allowEntryCode: values.allowEntryCode ?? true,
      };
      delete payload.instructor_eid;

      const updateRes = await fetch(
        `${process.env.REACT_APP_API_URL}/update_course`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );

      if (!updateRes.ok) throw new Error("Failed to update course");

      message.success("Course updated successfully!");
      navigate("/admin/courses");
    } catch (err) {
      console.error(err);
      message.error("Error saving course.");
    } finally {
      setSaving(false);
    }
  };

  const [removing, setRemoving] = useState(false);

  const handleRemove = async () => {
    setRemoving(true);
    try {
      const res = await fetch(
        `${process.env.REACT_APP_API_URL}/delete_course?course_id=${courseId}`,
        { method: "DELETE" }
      );
      if (!res.ok) throw new Error("Failed to delete course");

      message.success("Course deleted successfully!");
      navigate("/admin/courses");
    } catch (err) {
      console.error(err);
      message.error("Failed to delete course.");
    } finally {
      setRemoving(false);
    }
  };

  const handleRemoveStudent = async (studentId) => {
    try {
      const res = await fetch(
        `${process.env.REACT_APP_API_URL}/leave_course`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: studentId, course_id: courseId }),
        }
      );
      if (!res.ok) throw new Error("Failed to remove student");
      message.success("Student removed from course!");
      // Refresh enrolled students
      const studentsRes = await fetch(
        `${process.env.REACT_APP_API_URL}/get_course_enrollment?course_id=${courseId}`
      );
      if (studentsRes.ok) {
        const studentsData = await studentsRes.json();
        setEnrolledStudents(studentsData);
      }
    } catch (err) {
      console.error(err);
      message.error("Failed to remove student.");
    }
  };

  const handleEnrollStudent = async (values) => {
    try {
      // You need the student's ID, so you may want to search by EID or email
      // For this example, let's assume you enroll by EID:
      const res = await fetch(
        `${process.env.REACT_APP_API_URL}/get_user_by_eid?eid=${values.eid}`
      );
      if (!res.ok) throw new Error("Student not found");
      const student = await res.json();

      // Enroll the student
      const enrollRes = await fetch(
        `${process.env.REACT_APP_API_URL}/create_enrollment`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            student_id: student.id,
            course_id: courseId,
            role: "student", 
          }),
        }
      );
      if (!enrollRes.ok) throw new Error("Failed to enroll student");
      message.success("Student enrolled!");
      setShowAddStudent(false);

      // Refresh enrolled students
      const studentsRes = await fetch(
        `${process.env.REACT_APP_API_URL}/get_course_enrollment?course_id=${courseId}`
      );
      if (studentsRes.ok) {
        const studentsData = await studentsRes.json();
        setEnrolledStudents(studentsData);
      }
    } catch (err) {
      message.error("Failed to enroll student.");
    }
  };

  const studentColumns = [
    { title: "Name", dataIndex: "name", key: "name" },
    { title: "EID", dataIndex: "sis_user_id", key: "eid" },
    { title: "Email", dataIndex: "email_address", key: "email" },
    {
      title: "Actions",
      key: "actions",
      render: (_, record) => (
        <Popconfirm
          title="Remove Student"
          description="Are you sure you want to remove this student from the course?"
          onConfirm={() => handleRemoveStudent(record.id)}
          okText="Yes"
          cancelText="No"
        >
          <Button danger size="small">
            Remove
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <Spin spinning={loading}>
      <Card>
        <Title level={3}>Manage Course: {course?.name || "Loading..."}</Title>

        <Form layout="vertical" form={form} onFinish={handleSave}>
          <Form.Item
            label="Course Name"
            name="name"
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            label="Semester"
            name="semester"
            rules={[{ required: true }]}
          >
            <Select placeholder="Select semester">
              <Select.Option value="Spring">Spring</Select.Option>
              <Select.Option value="Summer">Summer</Select.Option>
              <Select.Option value="Fall">Fall</Select.Option>
              <Select.Option value="Winter">Winter</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="Year" name="year" rules={[{ required: true }]}>
            <Input type="number" />
          </Form.Item>

          <Form.Item
            label="Instructor EID"
            name="instructor_eid"
            rules={[
              { required: true, message: "Please enter the instructor EID" },
            ]}
          >
            <Input placeholder="e.g. abc123" />
          </Form.Item>

          <Form.Item label="Description" name="description">
            <Input.TextArea rows={3} />
          </Form.Item>

          <Form.Item
            label="Entry Code"
            name="entryCode"
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            label="Allow Entry Code"
            name="allowEntryCode"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Space>
            <Button type="primary" htmlType="submit" loading={saving}>
              Save Changes
            </Button>
            <Button onClick={() => navigate("/admin/courses")}>Cancel</Button>
            <Popconfirm
              title="Delete Course"
              description="This will permanently delete the course and all associated data. Are you sure?"
              onConfirm={handleRemove}
              okText="Yes"
              cancelText="No"
            >
              <Button danger loading={removing}>Delete Course</Button>
            </Popconfirm>
          </Space>
        </Form>

        <div style={{ marginTop: 32 }}>
          <Typography.Title level={4}>Enrolled Students</Typography.Title>
          <Space style={{ marginBottom: 16 }}>
            <Button type="primary" onClick={() => setShowAddStudent(true)}>
              Add Student
            </Button>
          </Space>
          <Table
            rowKey="id"
            columns={studentColumns}
            dataSource={enrolledStudents.filter((s) => s.role === "student")}
            pagination={false}
            locale={{ emptyText: "No students enrolled" }}
          />
        </div>
      </Card>

      <Modal
        title="Enroll Student"
        open={showAddStudent}
        onCancel={() => setShowAddStudent(false)}
        footer={null}
      >
        <Form
          layout="vertical"
          onFinish={async (values) => {
            try {
              // You need the student's ID, so you may want to search by EID or email
              // For this example, let's assume you enroll by EID:
              const res = await fetch(
                `${process.env.REACT_APP_API_URL}/get_user_by_eid?eid=${values.eid}`
              );
              if (!res.ok) throw new Error("Student not found");
              const student = await res.json();

              // Enroll the student
              const enrollRes = await fetch(
                `${process.env.REACT_APP_API_URL}/create_enrollment`,
                {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    student_id: student.id,
                    course_id: courseId,
                    role: "student", // <-- add this line
                  }),
                }
              );
              if (!enrollRes.ok) throw new Error("Failed to enroll student");
              message.success("Student enrolled!");
              setShowAddStudent(false);

              // Refresh enrolled students
              const studentsRes = await fetch(
                `${process.env.REACT_APP_API_URL}/get_course_enrollment?course_id=${courseId}`
              );
              if (studentsRes.ok) {
                const studentsData = await studentsRes.json();
                setEnrolledStudents(studentsData);
              }
            } catch (err) {
              message.error("Failed to enroll student.");
            }
          }}
        >
          <Form.Item
            label="Student EID"
            name="eid"
            rules={[
              { required: true, message: "Please enter the student's EID" },
            ]}
          >
            <Input placeholder="e.g. abc123" />
          </Form.Item>
          <Button type="primary" htmlType="submit">
            Enroll
          </Button>
        </Form>
      </Modal>
    </Spin>
  );
}
