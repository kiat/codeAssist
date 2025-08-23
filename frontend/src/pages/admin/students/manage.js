import { useState, useEffect } from "react";
import { Card, Form, Input, Button, Space, Typography, message, Popconfirm, Spin, Table } from "antd";
import { useParams, useNavigate } from "react-router-dom";

export default function AdminStudentManage() {
  const [student, setStudent] = useState(null);
  const [enrolledCourses, setEnrolledCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState(false);
  const { studentId } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();

  useEffect(() => {
    async function fetchStudent() {
      try {
        const res = await fetch(`${process.env.REACT_APP_API_URL}/get_user_by_id?id=${studentId}`);
        const data = await res.json();
        setStudent(data);
        form.setFieldsValue({
          name: data.name,
          sis_user_id: data.sis_user_id,
          email_address: data.email_address,
        });
        
        // Fetch enrolled courses
        const coursesRes = await fetch(`${process.env.REACT_APP_API_URL}/get_user_enrollments?user_id=${studentId}`);
        const coursesData = await coursesRes.json();
        setEnrolledCourses(coursesData);
      } catch (e) {
        message.error("Failed to fetch student");
      } finally {
        setLoading(false);
      }
    }
    fetchStudent();
  }, [studentId, form]);

  const handleSave = async (values) => {
    setSaving(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/admin_update_account`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: studentId,
          name: values.name,
          email_address: values.email_address,
          sis_user_id: values.sis_user_id,
        }),
      });
      if (res.ok) {
        message.success("Student updated successfully");
        setStudent({ ...student, ...values });
      } else {
        const error = await res.json();
        message.error(error.error || "Failed to update student");
      }
    } catch (e) {
      message.error("Failed to update student");
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async () => {
    //delete all data of this student
    setRemoving(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/delete_user?id=${studentId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        message.success("Student removed successfully");
        navigate("/admin/students");
      } else {
        message.error("Failed to remove student");
      }
    } catch (e) {
      message.error("Failed to remove student");
    } finally {
      setRemoving(false);
    }
  };

  const courseColumns = [
    { title: "Course Name", dataIndex: "name", key: "name" },
    { title: "Course ID", dataIndex: "id", key: "id" },
    { title: "Semester", dataIndex: "semester", key: "semester" },
    { title: "Year", dataIndex: "year", key: "year" },
  ];

  if (loading) return <Spin style={{ margin: 40 }} />;

  return (
    <Card>
      <Typography.Title level={3}>Manage Student: {student?.name}</Typography.Title>
      <Form form={form} onFinish={handleSave} layout="vertical">
        <Form.Item label="Name" name="name" rules={[{ required: true, message: "Name is required" }]}>
          <Input />
        </Form.Item>
        <Form.Item label="EID" name="sis_user_id" rules={[{ required: true, message: "EID is required" }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Email" name="email_address" rules={[{ required: true, message: "Email is required" }]}>
          <Input />
        </Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" loading={saving}>
            Save Changes
          </Button>
          <Button onClick={() => navigate("/admin/students")}>Cancel</Button>
          <Popconfirm
            title="Remove Student"
            description="This will completely remove the student from the system. All data including grades will be deleted. Are you sure?"
            onConfirm={handleRemove}
            okText="Yes"
            cancelText="No"
          >
            <Button danger loading={removing}>Remove Student</Button>
          </Popconfirm>
        </Space>
      </Form>
      
      <div style={{ marginTop: 32 }}>
        <Typography.Title level={4}>Enrolled Courses</Typography.Title>
        <Table 
          rowKey="id" 
          columns={courseColumns} 
          dataSource={enrolledCourses}
          pagination={false}
          locale={{ emptyText: "No courses enrolled" }}
        />
      </div>
    </Card>
  );
} 