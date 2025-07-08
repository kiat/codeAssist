import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Form, Input, Select, Button, Typography, Table, message, Spin, Space, } from "antd";

const { Title } = Typography;

export default function AdminCourseManage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const [course, setCourse] = useState(null);
  const [instructors, setInstructors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // TODO: Populate form fields after coding up backend
  
  return (
    <Card>
      <Title level={3}>Manage Course: {course?.name}</Title>

      <Form layout="vertical" form={form}>
        <Form.Item label="Course Name" name="name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>

        <Form.Item label="Semester" name="semester" rules={[{ required: true }]}>
          <Select>
            <Select.Option value="Spring">Spring</Select.Option>
            <Select.Option value="Summer">Summer</Select.Option>
            <Select.Option value="Fall">Fall</Select.Option>
            <Select.Option value="Winter">Winter</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="Year" name="year" rules={[{ required: true }]}>
          <Input type="number" />
        </Form.Item>

        <Form.Item label="Instructor" name="instructor_id" rules={[{ required: true }]}>
          <Select placeholder="Select instructor">
            {instructors.map((inst) => (
              <Select.Option key={inst.id} value={inst.id}>
                {inst.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Space>
          <Button type="primary" htmlType="submit" loading={saving}>
            Save Changes
          </Button>
          <Button onClick={() => navigate("/admin/courses")}>Cancel</Button>
        </Space>
      </Form>
    </Card>
  );
}