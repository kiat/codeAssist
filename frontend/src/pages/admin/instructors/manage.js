import { useState, useEffect } from "react";
import { Card, Form, Input, Button, Space, Typography, message, Popconfirm, Spin, Table } from "antd";
import { useParams, useNavigate } from "react-router-dom";

export default function AdminInstructorManage() {
  const [instructor, setInstructor] = useState(null);
  const [teachingCourses, setTeachingCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState(false);
  const { instructorId } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();

  useEffect(() => {
    async function fetchInstructor() {
      try {
        const res = await fetch(`${process.env.REACT_APP_API_URL}/get_user_by_id?id=${instructorId}`);
        const data = await res.json();
        setInstructor(data);
        form.setFieldsValue({
          name: data.name,
          sis_user_id: data.sis_user_id,
          email_address: data.email_address,
        });

        // Fetch courses taught by this instructor
        const coursesRes = await fetch(`${process.env.REACT_APP_API_URL}/get_courses_by_instructor?instructor_id=${instructorId}`);
        const coursesData = await coursesRes.json();
        setTeachingCourses(coursesData);
      } catch (e) {
        message.error("Failed to fetch instructor");
      } finally {
        setLoading(false);
      }
    }
    fetchInstructor();
  }, [instructorId, form]);

  const handleSave = async (values) => {
    setSaving(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/admin_update_account`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: instructorId,
          name: values.name,
          email_address: values.email_address,
          sis_user_id: values.sis_user_id,
        }),
      });
      if (res.ok) {
        message.success("Instructor updated successfully");
        setInstructor({ ...instructor, ...values });
      } else {
        const error = await res.json();
        message.error(error.error || "Failed to update instructor");
      }
    } catch (e) {
      message.error("Failed to update instructor");
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async () => {
    setRemoving(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/delete_user?id=${instructorId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        message.success("Instructor removed successfully");
        navigate("/admin/instructors");
      } else {
        message.error("Failed to remove instructor");
      }
    } catch (e) {
      message.error("Failed to remove instructor");
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
      <Typography.Title level={3}>Manage Instructor: {instructor?.name}</Typography.Title>
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
          <Button onClick={() => navigate("/admin/instructors")}>Cancel</Button>
          <Popconfirm
            title="Remove Instructor"
            description="This will completely remove the instructor from the system. All data including courses will be deleted. Are you sure?"
            onConfirm={handleRemove}
            okText="Yes"
            cancelText="No"
          >
            <Button danger loading={removing}>Remove Instructor</Button>
          </Popconfirm>
        </Space>
      </Form>

      <div style={{ marginTop: 32 }}>
        <Typography.Title level={4}>Courses Taught</Typography.Title>
        <Table
          rowKey="id"
          columns={courseColumns}
          dataSource={teachingCourses}
          pagination={false}
          locale={{ emptyText: "No courses taught" }}
        />
      </div>
    </Card>
  );
}