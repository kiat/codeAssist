import { PageHeader, Card, Row, Col, Statistic } from "antd";
import { UserOutlined, BookOutlined, TeamOutlined } from "@ant-design/icons";
import { useCallback, useContext, useEffect, useState } from "react";
import { GlobalContext } from "../../../App";
import PageContent from "../../../components/layout/pageContent";
import PageBottom from "../../../components/layout/pageBottom";

export default function AdminDashboard() {
  const { userInfo } = useContext(GlobalContext);
  const [stats, setStats] = useState({
    totalCourses: 0,
    totalInstructors: 0,
    totalStudents: 0
  });

  // Fetch statistics
  const fetchStats = useCallback(async () => {
    try {
      // TODO: Implement these API endpoints
      const coursesRes = await fetch(`${process.env.REACT_APP_API_URL}/get_all_courses`);
      const instructorsRes = await fetch(`${process.env.REACT_APP_API_URL}/get_all_instructors`);
      const studentsRes = await fetch(`${process.env.REACT_APP_API_URL}/get_all_students`);

      const courses = await coursesRes.json();
      const instructors = await instructorsRes.json();
      const students = await studentsRes.json();

      setStats({
        totalCourses: courses.length,
        totalInstructors: instructors.length,
        totalStudents: students.length
      });
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return (
    <>
      <PageContent>
        <PageHeader title="Admin Dashboard" />
        <Row gutter={[16, 16]}>
          <Col span={8}>
            <Card>
              <Statistic
                title="Total Courses"
                value={stats.totalCourses}
                prefix={<BookOutlined />}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="Total Instructors"
                value={stats.totalInstructors}
                prefix={<TeamOutlined />}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="Total Students"
                value={stats.totalStudents}
                prefix={<UserOutlined />}
              />
            </Card>
          </Col>
        </Row>
      </PageContent>
      {/* <PageBottom>
        <div style={{ color: "white" }}>
          Welcome, {userInfo?.name}
        </div>
      </PageBottom> */}
    </>
  );
} 