import { useState } from "react";
import { Card, Form, Input, Button, Space, Typography, message, Alert } from "antd";
import { useNavigate } from "react-router-dom";

export default function AdminInstructorAdd() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/create_user`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: values.name,
          email_address: values.email,
          eid: values.eid,
          role: "instructor", 
          password: values.password,
        }),
      });
      if (res.ok) {
        message.success("Instructor created successfully");
        navigate("/admin/instructors"); 
      } else {
        const error = await res.json();
        message.error(error.message || error.error || "Failed to create instructor");
      }
    } catch (e) {
      message.error("Failed to create instructor");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <Typography.Title level={3}>Add New Instructor</Typography.Title>
      <Alert
        message="Temporary password"
        description="Share this password with the instructor privately and ask them to change it after their first login (Account settings)."
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
        <Form.Item
          label="Temporary Password"
          name="password"
          rules={[
            { required: true, message: "Temporary password is required" },
            { min: 8, message: "Use at least 8 characters" },
          ]}
        >
          <Input.Password autoComplete="new-password" />
        </Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" loading={loading}>
            Create Instructor
          </Button>
          <Button onClick={() => navigate("/admin/instructors")}>Cancel</Button>
        </Space>
      </Form>
    </Card>
  );
}