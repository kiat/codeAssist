import {
  CheckOutlined,
  DownloadOutlined,
  EyeOutlined,
  RightOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Button, PageHeader, Space, Table, Typography, Card, Input } from "antd";
import { useState, useEffect, useCallback, useContext, } from "react";
import { formatDayTimeEn } from "../../common/format";
import PageBottom from "../../components/layout/pageBottom";
import PageContent from "../../components/layout/pageContent";
import ExportSubmissions from "./ExportSubmissions";
import PublishGradesModal from "./PublishGradesModal";
import { GlobalContext } from "../../App";
import { useNavigate, useParams } from "react-router-dom";


export default () => {
  const [downloadModalOpen, setDownloadModalOpen] = useState(false);
  const [publishModalOpen, setPublishModalOpen] = useState(false);
  const [submissions, setSubmissions] = useState([]);
  const [gradePublishState, setGradePublishState] = useState({
    hold_grades: false,
    grades_published: false,
  });
  const { assignmentInfo } = useContext(GlobalContext);
  const { userInfo, courseInfo } = useContext(GlobalContext);
  const navigate = useNavigate();
  const { assignmentId } = useParams();
  const [searchText, setSearchText] = useState("");

  const togglePublishModalOpen = useCallback(() => {
    setPublishModalOpen(t => !t);
  }, []);

  const handlePublishSuccess = useCallback((data) => {
    setGradePublishState(prev => ({ ...prev, grades_published: data.grades_published }));
  }, []);

  const toggleDownloadModalOpen = useCallback(() => {
    setDownloadModalOpen(t => !t);
  }, []);

  const goAssignmentResult = (submissionId) => {
    navigate(`/assignmentResult/${submissionId}`);
  };

  const handleDownloadGrades = useCallback(async () => {
    try {
      const res = await fetch(
        `${process.env.REACT_APP_API_URL}/export_grades_csv?assignment_id=${assignmentId}`,
        { credentials: "include" }
      );
      if (!res.ok) {
        throw new Error("Failed to download grades.");
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${assignmentInfo?.name || "assignment"}_grades.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Error downloading grades:", err);
    }
  }, [assignmentId, assignmentInfo]);

  const columns = [
    {
      title: "FIRST & LAST NAME",
      dataIndex: "student_name",
      render: (_, record) =>
        record.submissionId ? (
        <Typography.Link onClick={() => goAssignmentResult(record.submissionId)}> 
          {record.student_name}
        </Typography.Link>
        ) : (
          record.student_name
      ),
      sorter: (a, b) => a.student_name.localeCompare(b.student_name),
    },
    {
      title: "EMAIL",
      dataIndex: "email_address",
      render: (text) => <Typography.Link>{text}</Typography.Link>,
      sorter: (a, b) => a.email_address.localeCompare(b.email_address),
    },
    {
      title: "SCORE",
      dataIndex: "score",
      align: "center",
      render: (score) => 
        (score != null ? score : "-"),
      sorter: (a, b) => (a.score ?? -1) - (b.score ?? -1),
    },
    {
      title: "GRADED",
      dataIndex: "graded",
      align: "center",
      render: (graded) => 
        graded ? <CheckOutlined style={{ color: "#189eff" }} /> : null,
      sorter: (a, b) => 
        a.graded === b.graded ? 0 : a.graded ? - 1 : 1,
    },
    {
      title: "VIEWED",
      dataIndex: "viewed",
      align: "center",
      render: text => <EyeOutlined style={{ color: text ? "#189eff" : "" }} />,
      sorter: (a, b) => 
        a.viewed === b.viewed ? 0 : a.viewed ? -1 : 1,
    },
    {
      title: "TIME(CST)",
      dataIndex: "submitted_at",
      render: (ts) => 
        ts ? formatDayTimeEn(ts) : "",
      sorter: (a, b) => {
        if (!a.submitted_at) {
          return -1;
        }
        if (!b.submitted_at) {
          return 1;
        }
        return (
          new Date(a.submitted_at) - new Date(b.submitted_at)
        );
      }
    },
  ];

  useEffect(() => {
    if (!userInfo || !userInfo.id) {
      navigate('/');
      return;
    }
    if (!courseInfo?.id || !assignmentId) {
      console.error('No course info or assignment_id provided');
      return;
    }

    (async () => {
      try {
        // Grade publish state for this assignment (hold_grades is fixed at
        // creation; grades_published is what the Publish/Unpublish button toggles)
        const assignmentRes = await fetch(
          `${process.env.REACT_APP_API_URL}/get_assignment?assignment_id=${assignmentId}`,
          { credentials: "include" }
        );
        if (assignmentRes.ok) {
          const assignmentData = await assignmentRes.json();
          setGradePublishState({
            hold_grades: Boolean(assignmentData.hold_grades),
            grades_published: Boolean(assignmentData.grades_published),
          });
        }

        // First get all submissions
        const allSubmissions = await fetch(
          `${process.env.REACT_APP_API_URL}/get_all_assignment_submissions?assignment_id=${assignmentId}`,
          { credentials: "include" }
        );
        if (!allSubmissions.ok) {
          throw new Error("Failed to load all submissions.");
        }
        const allSubs = await allSubmissions.json();

        // Now fetch all the students
        const students = await fetch(
          `${process.env.REACT_APP_API_URL}/get_course_enrollment?course_id=${courseInfo.id}`,
          { credentials: "include" }
        );
        if (!students.ok) {
          throw new Error("Failed to load students list.");
        }
        const allRes = await students.json();
        // Getting rid of the instructor from the enrolled list
        const allStudents = allRes.filter(s => s.id !== userInfo.id);

        // Group the submissions by student (matching students and their submissions)
        const subsByStudent = allSubs.reduce((acc, sub) => {
          (acc[sub.student_id] = acc[sub.student_id] || []).push(sub);
          return acc
        }, {});

        // Get active score and build rows for each student
        const rows = allStudents.map((stu) => {
          const subs = subsByStudent[stu.id] || [];
          const activeSub = subs.find((s) => s.active) || null;

          return {
            student_name: stu.name,
            email_address: stu.email_address,
            score: activeSub?.score ?? null,
            submitted_at: activeSub?.submitted_at ?? null,
            graded: Boolean(activeSub),
            viewed: Boolean(activeSub),
            submissionId: activeSub?.id ?? null,
          };
        });

        setSubmissions(rows);
      } catch (err) {
        console.error("Error fetching grades:", err);
      }
    })();
  }, [
    userInfo,
    courseInfo,
    assignmentId,
    navigate,
  ]);

  const filteredSubmissions = submissions.filter((row) => {
    const q = searchText.trim().toLowerCase();
    if (!q) return true;
    return (
      row.student_name.toLowerCase().includes(q) ||
      row.email_address.toLowerCase().includes(q)
    );
  });

  return (
    <>
      <PageContent>
        <PageHeader title={`Review Grades for ${assignmentInfo?.name}`} />
          <Card
            bordered={false}
            bodyStyle={{ padding: 0 }}
            title={
              <Space align="center">
                <UserOutlined style={{ fontSize: 18 }} />
                <Typography.Title level={4} style={{ margin: 0 }}>
                  {filteredSubmissions.length} students
                </Typography.Title>
              </Space>
            }
            extra={
              <Input.Search
                placeholder="Search by name or email address"
                allowClear
                onSearch={val => setSearchText(val)}
                style={{ width: 300 }}
                />
            }
          />
          <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
            <Table
              columns={columns}
              dataSource={filteredSubmissions}
              rowKey="email_address"
            />
          </Card>
      </PageContent>
      <PageBottom>
        <Space>
          <Button icon={<DownloadOutlined />} onClick={handleDownloadGrades}>
            Download Grades
          </Button>
          <Button icon={<DownloadOutlined />} >
            Export Evaluations
          </Button>
          <Button icon={<DownloadOutlined />} onClick={toggleDownloadModalOpen}>
            Export Submissions
          </Button>
          {gradePublishState.hold_grades && (
            <Button onClick={togglePublishModalOpen}>
              <span>
                {gradePublishState.grades_published ? "Unpublish Grades" : "Publish Grades"}
              </span>
              <RightOutlined />
            </Button>
          )}
        </Space>
      </PageBottom>
      <ExportSubmissions
        open={downloadModalOpen}
        onCancel={toggleDownloadModalOpen}
        assignmentId={assignmentId}
      />
      <PublishGradesModal
        open={publishModalOpen}
        onCancel={togglePublishModalOpen}
        assignmentId={assignmentId}
        published={gradePublishState.grades_published}
        studentCount={filteredSubmissions.length}
        onSuccess={handlePublishSuccess}
      />
    </>
  );
};
