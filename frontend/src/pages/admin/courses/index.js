import { useEffect, useState } from "react";
import { Input, Table, PageHeader, Card, Space, Button, Switch, message, } from "antd";
import { useNavigate } from "react-router-dom";

export default function AdminCourses() {
  const [courses, setCourses] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [vertexSaving, setVertexSaving] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${process.env.REACT_APP_API_URL}/get_all_courses`, { credentials: "include" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const withInstructorNames = await Promise.all(
          data.map(async course => {
            try {
              const res = await fetch(`${process.env.REACT_APP_API_URL}/get_user_by_id?id=${course.instructor_id}`, { credentials: "include" });
              const userData = await res.json();
              return { ...course, instructor_name: userData.name || course.instructor_id };
            } catch {
              return { ...course, instructor_name: course.instructor_id };
            }
          })
        );

        setCourses(withInstructorNames);
      } catch (e) {
        message.error("Failed to fetch courses");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const term = search.trim().toLowerCase();
  const filtered = term
    ? courses.filter(c =>
      c.name?.toLowerCase().includes(term) ||
      c.id?.toLowerCase().includes(term) ||
      c.semester?.toLowerCase().includes(term) ||
      c.year?.toString().includes(term) ||
      c.instructor_name?.toLowerCase().includes(term)
    )
    : courses;


  const setVertexEnabled = async (courseId, enabled) => {
    setVertexSaving(courseId);
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/admin_set_course_vertex`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ course_id: courseId, enabled }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setCourses(prev =>
        prev.map(c => (c.id === courseId ? { ...c, vertex_enabled: enabled } : c))
      );
      message.success(enabled ? "Vertex AI enabled for this course" : "Vertex AI disabled for this course");
    } catch (e) {
      message.error("Failed to update Vertex AI access");
    } finally {
      setVertexSaving(null);
    }
  };

  const columns = [
    { title: "Course Name", dataIndex: "name", key: "name" },
    { title: "Course ID", dataIndex: "id", key: "id" },
    { title: "Semester", dataIndex: "semester", key: "semester" },
    { title: "Year", dataIndex: "year", key: "year" },
    { title: "Instructor", dataIndex: "instructor_name", key: "instructor" },
    {
      title: "Vertex AI",
      key: "vertex_enabled",
      render: (_, course) => (
        <Switch
          aria-label={`Vertex AI for ${course.name}`}
          checked={!!course.vertex_enabled}
          loading={vertexSaving === course.id}
          onChange={checked => setVertexEnabled(course.id, checked)}
        />
      ),
    },
  ];
  

  return (
    <Card>
      <PageHeader title="Search Courses" />
      <Space direction="vertical" style={{ width: "100%" }}>
        <Space>
          <Input.Search
            placeholder="Search by name, course ID, semester, year, or instructor name"
            value={search}
            onChange={e => setSearch(e.target.value)}
            enterButton
            style={{ width: 500 }}
            onSearch={setSearch}
          />
          <Button type="default" onClick={() => navigate("/admin/courses/create")}>Add Course</Button>
        </Space>
        <Table rowKey="id" columns={columns} dataSource={filtered} loading={loading} />
      </Space>
    </Card>
  );
} 