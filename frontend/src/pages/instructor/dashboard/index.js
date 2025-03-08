// import { ExclamationCircleFilled } from "@ant-design/icons";
import {
  Button,
  Card,
  Descriptions,
  Divider,
  PageHeader,
  Progress,
  Table,
} from "antd";
import moment from "moment";
import { Link, useParams } from "react-router-dom";
import { useContext } from "react";
import { GlobalContext } from "../../../App";
import { useEffect, useState } from "react";
import { getCourseAssignments } from "../../../services/course";

//for now change this to a course_id you have in the database
const columns = [
  {
    title: "ACTIVE ASSIGNMENTS",
    dataIndex: "name",
    sorter: (a, b) => a.assignmentName > b.assignmentName,
    render: (text, record) => (
      <Link to={`/assignment/reviewGrades/${record.id}`}>{text}</Link>
    ),
  },
  {
    title: "RELEASED",
    dataIndex: "published_date",
    sorter: (a, b) => a.released - b.released,
    render: (text) => moment(text + "Z").format("MMM DD [AT] h:mmA").toUpperCase(),
  },
  {
    title: "DUE(CDT)",
    dataIndex: "due_date",
    sorter: (a, b) => a.due - b.due,
    render: (text) => moment(text + "Z").format("MMM DD [AT] h:mmA").toUpperCase(),
  },
  {
    title: "SUBMISSIONS",
    dataIndex: "submissions",
    sorter: (a, b) => a.submissions - b.submissions,
  },
  {
    title: "% GRADED",
    dataIndex: "graded",
    sorter: (a, b) => a.graded - b.graded,
    render: (text) => <Progress percent={text} size="small" status="normal" />,
  },
  {
    title: "PUBLISHED",
    dataIndex: "published",
    sorter: (a, b) => a.published - b.published,
    render: (text) => (
      <Button type={text ? "primary" : "default"} shape="circle" size="small">
        {" "}
      </Button>
    ),
  },
  {
    title: "REGRADES",
    dataIndex: "regrades",
    sorter: (a, b) => a.regrades - b.regrades,
  },
];

export default function InstructorDashboard() {
  const { courseId } = useParams();
  const [ data, setData] = useState([]);
  const { courseInfo, updateCourseInfo } = useContext(GlobalContext);

  // const fetchData = async (endpoint, params) => {
  //   try {
  //     const response = await fetch(`${process.env.REACT_APP_API_URL}${endpoint}?${new URLSearchParams(params)}`);
  //     if (!response.ok) throw new Error('Network response was not ok.');
  //     return await response.json();
  //   } catch (error) {
  //     console.error('There has been a problem with your fetch operation:', error);
  //   }
  // };
  
  useEffect(() => {
    const initCourseAssignments = async () => {
      try {
        const res = await getCourseAssignments({ course_id: courseId });
        setData(res.data);
      } catch (error) {
        console.error("Error fetching course assignments:", error);
      }
      
      // redundant call to get course info
      // if (!courseInfo.id || !courseInfo.name || !courseInfo.year || !courseInfo.semester || !courseInfo.entryCode || !courseInfo.description) {
      //   const courseDetails = await fetchData("/get_course_info", { course_id: courseId });
      //   if (courseDetails && courseDetails.length > 0) {
      //     const [detail] = courseDetails;
      //     updateCourseInfo({ ...detail, id: courseId });
      //   }
      // }
    };
    initCourseAssignments();
  }, [courseId, courseInfo.id, courseInfo.name, courseInfo.year, courseInfo.semester, courseInfo.entryCode, courseInfo.description, updateCourseInfo]);

  if (!courseInfo.id) return null;

  return (
    <>
      <PageHeader title={courseInfo.name} subTitle={`${courseInfo.semester} ${courseInfo.year}`}>
        <Descriptions>
          <Descriptions.Item label="Course ID">{courseId}</Descriptions.Item>
        </Descriptions>
      </PageHeader>
      <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
        <h3>DESCRIPTION</h3>
        <Divider style={{ marginTop: 0, marginBottom: "5px" }} />
        <div>
          {courseInfo.description === "" ? (
            <div>
              <span>Edit your course description on the </span>
              <Link to={`/courseSettings/${courseId}`}>Course Settings</Link>
              <span> page.</span>
            </div>
          ) : (
            <span>{`${courseInfo.description}`}</span>
          )}
        </div>
      </Card>
      <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
        <h3>ASSIGNMENTS</h3>
        <Divider style={{ marginTop: 0, marginBottom: "5px" }} />
      </Card>
      <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
        <Table rowKey="id" columns={columns} dataSource={data} />
      </Card>
    </>
  );
}