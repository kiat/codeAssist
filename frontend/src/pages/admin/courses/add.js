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
      // Get instructor_id from EID
      const eid = values.instructor_eid;
      const res = await fetch(`${process.env.REACT_APP_API_URL}/get_instructor_by_eid?eid=${eid}`);
      if (!res.ok) throw new Error("Instructor not found");
      const instructor = await res.json();
  
      const payload = {
        ...values,
        instructor_id: instructor.id,
      };
      delete payload.instructor_eid;
  
      const createRes = await fetch(`${process.env.REACT_APP_API_URL}/create_course`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
  
      if (createRes.status === 409) {
        message.error("Entry code already exists. Please use a unique code.");
        return;
      }
  
      if (!createRes.ok) {
        throw new Error("Unknown error while creating course");
      }
  
      message.success("Course created successfully");
      navigate("/admin/courses/all");
    } catch (err) {
      console.error(err);
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
          name="instructor_eid"
          label="Instructor EID"
          rules={[{ required: true, message: "Please enter the instructor EID" }]}
        >
          <Input placeholder="e.g. abc123" />
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
