import { useState } from "react";
import { Card, Form, Input, Button, Space, Typography, message, Alert } from "antd";
import { useNavigate } from "react-router-dom";

export default function AdminStudentAdd() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/create_user`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: values.name,
          email_address: values.email,
          eid: values.eid,
          role: "student",
          password: "123456", //set initial password
        }),
      });
      if (res.ok) {
        message.success("Student created successfully");
        navigate("/admin/students");
      } else {
        const error = await res.json();
        message.error(error.error || "Failed to create student");
      }
    } catch (e) {
      message.error("Failed to create student");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <Typography.Title level={3}>Add New Student</Typography.Title>
      <Alert
        message="Initial Password"
        description="The student's initial password will be set to: 123456"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      <Form form={form} onFinish={handleSubmit} layout="vertical">
        <Form.Item label="Name" name="name" rules={[{ required: true, message: "Name is required" }]}>
          <Input />
        </Form.Item>
        <Form.Item label="EID" name="eid" rules={[{ required: true, message: "EID is required" }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Email" name="email" rules={[{ required: true, message: "Email is required" }]}>
          <Input />
        </Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" loading={loading}>
            Create Student
          </Button>
          <Button onClick={() => navigate("/admin/students")}>Cancel</Button>
        </Space>
      </Form>
    </Card>
  );
} 