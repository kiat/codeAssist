import {
  CheckOutlined,
  DownloadOutlined,
  EyeOutlined,
  RightOutlined,
} from "@ant-design/icons";
import { Button, PageHeader, Space, Table, Typography } from "antd";
import { useState, useEffect } from "react";
import { formatDayTimeEn } from "../../common/format";
import { GRADES } from "./mock";
import PageBottom from "../../components/layout/pageBottom";
import PageContent from "../../components/layout/pageContent";
import PopoverDownload from "../../components/download/PopoverDownload";
import DownloadSubmissions from "./DownloadSubmissions";
import { useCallback } from "react";
import { useContext } from "react";
import { GlobalContext } from "../../App";
import { useNavigate, useParams } from "react-router-dom";


export default () => {
  const [assignmentDetail, setAssignmentDetail] = useState();
  const [downloadModalOpen, setDownloadModalOpen] = useState(false);
  const [submissions, setSubmissions] = useState([]);
  const { assignmentInfo, updateAssignmentInfo } = useContext(GlobalContext);
  const { userInfo, courseInfo } = useContext(GlobalContext);
  const navigate = useNavigate();
  const { assignmentId } = useParams();

  const toggleDownloadModalOpen = useCallback(() => {
    setDownloadModalOpen(t => !t);
  }, []);


  const sharedCell = record => {
    if (record.score) {
      return {};
    }
    return {
      colSpan: 0,
    };
  };

  const goAssignmentResult = name => {
    updateAssignmentInfo({
      ...assignmentInfo,
      studentName: name,
    });
    navigate(`/assignmentResult/${assignmentInfo.id}`);
  };
  
// TODO: clicking students name shouldn't link to the same page as a student view
  const columns = [
    {
      title: "FIRST & LAST NAME",
      dataIndex: "student_name",
      render: text => (
        <Typography.Link onClick={() => goAssignmentResult(text)}> 
          {text}
        </Typography.Link>
      ),
      sorter: (a, b) => a.username > b.username,
    },
    {
      title: "EMAIL",
      dataIndex: "email_address",
      render: text => <Typography.Link>{text}</Typography.Link>,
      sorter: (a, b) => a.email > b.email,
    },
    {
      title: "SCORE",
      dataIndex: "score",
      align: "center",
      onCell: record => {
        if (record.score) {
          return {};
        } else {
          return {
            colSpan: 4,
          };
        }
      },
      render: text => (text ? text : "This student doesn't have a submission."),
      sorter: (a, b) => a.score - b.score,
    },
    {
      title: "GRADED",
      dataIndex: "graded",
      align: "center",
      render: text => (
        <CheckOutlined style={{ color: text ? "#189eff" : "" }} />
      ),
      onCell: sharedCell,
      sorter: (a, b) => a.graded - b.graded,
    },
    {
      title: "VIEWED",
      dataIndex: "viewed",
      align: "center",
      render: text => <EyeOutlined style={{ color: text ? "#189eff" : "" }} />,
      onCell: sharedCell,
      sorter: (a, b) => a.viewed - b.viewed,
    },
    {
      title: "TIME(CST)",
      dataIndex: "executed_at",
      render: text => formatDayTimeEn(text),
      onCell: sharedCell,
      sorter: (a, b) => a.time - b.time,
    },
  ];



  useEffect(() => {
    if (!userInfo || !userInfo.id) {
      navigate('/');
      return;
    }
    if (!assignmentId) {
      console.error('No assignment_id provided');
      return;
    }

    fetch(`${process.env.REACT_APP_API_URL}/get_course_assignment_latest_submissions?` +
      new URLSearchParams({
        course_id: courseInfo.id,
        assignment_id: assignmentId }))
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        setSubmissions(data);
      })
      .catch(error => {
        console.error('There was a problem with the fetch:', error);
      });
  }, [assignmentId, navigate, userInfo, courseInfo]);

  return (
    <>
      <PageContent>
        <PageHeader title={`Review Grades for ${assignmentInfo?.name}`} />
        <Table
          columns={columns}
          dataSource={submissions}
          rowKey="id"
          style={{ marginLeft: "10px" }}
        />
      </PageContent>
      <PageBottom>
        {/* ... */}
      </PageBottom>
      <DownloadSubmissions
        open={downloadModalOpen}
        onCancel={toggleDownloadModalOpen}
      />
    </>
  );
};
