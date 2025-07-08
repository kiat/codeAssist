import { useState } from "react";
import { Input, Table, PageHeader, Card, Space, Button, message, } from "antd";
import { useNavigate } from "react-router-dom";

export default function AdminCourses() {
  const [courses, setCourses] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async () => {
    if (!search.trim()) {
      message.info("Please enter a search term.");
      return;
    }
    setLoading(true);
    setSearched(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/get_all_courses`);
      const data = await res.json();
      console.log("Fetched courses:", data);

      const withInstructorNames = await Promise.all(
        data.map(async course => {
          try {
            const res = await fetch(`${process.env.REACT_APP_API_URL}/get_user_by_id?id=${course.instructor_id}`);
            const userData = await res.json();
            return { ...course, instructor_name: userData.name || course.instructor_id };
          } catch {
            return { ...course, instructor_name: course.instructor_id };
          }
        })
      );

      const filtered = withInstructorNames.filter(c =>
        c.name?.toLowerCase().includes(search.toLowerCase()) ||
        c.id?.toLowerCase().includes(search.toLowerCase()) ||
        c.semester?.toLowerCase().includes(search.toLowerCase()) ||
        c.year?.toString().includes(search) ||
        c.instructor_name?.toLowerCase().includes(search.toLowerCase())
      );

      setCourses(filtered);
    } catch (e) {
      message.error("Failed to fetch courses");
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: "Course Name", dataIndex: "name", key: "name" },
    { title: "Course ID", dataIndex: "id", key: "id" },
    { title: "Semester", dataIndex: "semester", key: "semester" },
    { title: "Year", dataIndex: "year", key: "year" },
    { title: "Instructor", dataIndex: "instructor_name", key: "instructor_name" },
    {
      title: "Actions",
      key: "actions",
      render: (_, record) => (
        <Button type="link" onClick={() => navigate(`/admin/courses/${record.id}/manage`)}>Manage</Button>
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
            loading={loading}
            onSearch={handleSearch}
          />
          <Button type="default" onClick={() => navigate("/admin/courses/all")}>View All Courses</Button>
        </Space>
        <Table rowKey="id" columns={columns} dataSource={searched ? courses : []} loading={loading} />
      </Space>
    </Card>
  );
} 