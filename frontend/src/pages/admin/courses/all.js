import { useEffect, useState } from "react";
import { Card, Table, Typography, Divider, Spin, message } from "antd";

export default function AdminAllCourses() {
  const [coursesByTerm, setCoursesByTerm] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchCourses() {
      setLoading(true);
      try {
        const res = await fetch(`${process.env.REACT_APP_API_URL}/get_all_courses`);
        const data = await res.json();
        // Fetch instructor names for all courses
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
        // Group by term (semester + year)
        const grouped = {};
        withInstructorNames.forEach(course => {
          const term = `${course.semester} ${course.year}`;
          if (!grouped[term]) grouped[term] = [];
          grouped[term].push(course);
        });
        setCoursesByTerm(grouped);
      } catch (e) {
        message.error("Failed to fetch courses");
      } finally {
        setLoading(false);
      }
    }
    fetchCourses();
  }, []);

  const columns = [
    { title: "Course Name", dataIndex: "name", key: "name" },
    { title: "Course ID", dataIndex: "id", key: "id" },
    { title: "Instructor", dataIndex: "instructor_name", key: "instructor_name" },
  ];

  if (loading) return <Spin style={{ margin: 40 }} />;

  return (
    <Card>
      <Typography.Title level={3}>All Courses by Term</Typography.Title>
      {Object.keys(coursesByTerm).sort((a, b) => {
        // Sort by year desc, then semester order
        const [semA, yearA] = a.split(" ");
        const [semB, yearB] = b.split(" ");
        const semesterOrder = { Spring: 1, Summer: 2, Fall: 3, Winter: 4 };
        if (yearA !== yearB) return parseInt(yearB) - parseInt(yearA);
        return semesterOrder[semA] - semesterOrder[semB];
      }).map(term => (
        <div key={term} style={{ marginBottom: 32 }}>
          <Divider orientation="left"><Typography.Title level={4}>{term}</Typography.Title></Divider>
          <Table
            rowKey="id"
            columns={columns}
            dataSource={coursesByTerm[term]}
            pagination={false}
          />
        </div>
      ))}
    </Card>
  );
} 