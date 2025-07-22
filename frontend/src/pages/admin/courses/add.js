import { useState } from "react";
import { Card, Form, Input, Select, Button, message, Checkbox } from "antd";
import { useNavigate } from "react-router-dom";

export default function AdminCourseAdd() {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/create_course`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      if (!res.ok) throw new Error();
      message.success("Course created successfully");
      navigate("/admin/courses/all");
    } catch {
      message.error("Failed to create course");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Add New Course">
      <Form layout="vertical" form={form} onFinish={onFinish}>
        <Form.Item name="name" label="Course Name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>

        <Form.Item name="semester" label="Semester" rules={[{ required: true }]}>
          <Select placeholder="Select a semester">
            <Select.Option value="Fall">Fall</Select.Option>
            <Select.Option value="Spring">Spring</Select.Option>
            <Select.Option value="Summer">Summer</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item name="year" label="Year" rules={[{ required: true }]}>
          <Input />
        </Form.Item>

        <Form.Item name="entryCode" label="Entry Code" rules={[{ required: true }]}>
          <Input />
        </Form.Item>

        <Form.Item
          name="instructor_id"
          label="Instructor ID"
          rules={[{ required: true, message: "Please enter the instructor ID" }]}
        >
          <Input placeholder="e.g. 12345" />
        </Form.Item>

        <Form.Item name="allowEntryCode" valuePropName="checked" initialValue={true}>
          <Checkbox>Allow students to join with Entry Code</Checkbox>
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            Create Course
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}
