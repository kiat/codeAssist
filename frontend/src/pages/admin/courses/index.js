import { useEffect, useState } from "react";
import { Input, Table, PageHeader, Card, Space, Button, message, } from "antd";
import { useNavigate } from "react-router-dom";

export default function AdminCourses() {
  const [courses, setCourses] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
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


  const columns = [
    { title: "Course Name", dataIndex: "name", key: "name" },
    { title: "Course ID", dataIndex: "id", key: "id" },
    { title: "Semester", dataIndex: "semester", key: "semester" },
    { title: "Year", dataIndex: "year", key: "year" },
    { title: "Instructor", dataIndex: "instructor_name", key: "instructor" }, // adjust key if needed
    {
      title: "Actions",
      key: "actions",
      render: (_, record) => (
        <Button
          type="primary"
          onClick={() => navigate(`/admin/courses/${record.id}/manage`)}
        >
          Manage
        </Button>
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
          <Button type="primary" onClick={() => navigate("/admin/courses/all")}>View All Courses</Button>
        </Space>
        <Table rowKey="id" columns={columns} dataSource={filtered} loading={loading} />
      </Space>
    </Card>
  );
} 