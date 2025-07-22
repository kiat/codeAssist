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
  Popconfirm
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
        form.setFieldsValue({
          ...courseObj,
          description: courseObj.description || "",
          entryCode: courseObj.entryCode || "",
          allowEntryCode: courseObj.allowEntryCode ?? true,
        });

        // Fetch instructors
        const instRes = await fetch(
          `${process.env.REACT_APP_API_URL}/get_all_instructors`
        );
        const instructorsData = await instRes.json();
        setInstructors(instructorsData);
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

      const payload = {
        ...values,
        course_id: courseId,
        description: values.description || "",
        entryCode: values.entryCode || "",
        allowEntryCode: values.allowEntryCode ?? true,
      };

      const res = await fetch(
        `${process.env.REACT_APP_API_URL}/update_course`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );

      if (!res.ok) throw new Error("Failed to update course");

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
            label="Instructor"
            name="instructor_id"
            rules={[{ required: true }]}
          >
            <Select placeholder="Select instructor">
              {instructors.map((inst) => (
                <Select.Option key={inst.id} value={inst.id}>
                  {inst.name}
                </Select.Option>
              ))}
            </Select>
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
      </Card>
    </Spin>
  );
}
