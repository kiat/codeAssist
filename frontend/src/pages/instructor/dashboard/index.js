// import { ExclamationCircleFilled } from "@ant-design/icons";
import {
  Button,
  Card,
  Descriptions,
  Divider,
  PageHeader,
  Progress,
  Space,
  Table,
} from "antd";
import { texts } from "./constant";
import TextItem from "./TextItem";
import moment from "moment";
import { Link, useParams } from "react-router-dom";
import { useContext } from "react";
import { GlobalContext } from "../../../App";
import { useEffect, useState } from "react";
const api_url = process.env.REACT_APP_API_URL + "/get_course_assignments";
const course_id = "577031b8-ac04-4c33-84bf-32a82c2ce5ba"; //need to figure out how to find global course_id,
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
  const [data, setData] = useState(null);
  const { courseInfo, updateCourseInfo } = useContext(GlobalContext);
  const user_id = useContext(GlobalContext).userInfo.id;
  const [description, setDescription] = useState("");

  //   async function get(url, params){
  //     let response = await fetch(url + '?' + new URLSearchParams(params))
  //     let data = await response.json()
  //     data = JSON.stringify(data)
  //     return JSON.parse(data)
  // }

  //   function main() {
  //     //OPTION 1

  //     //OPTION 2
  //     let jsondata = get('http://localhost:5000/get_course_assignments', {
  //       course_id: "577031b8-ac04-4c33-84bf-32a82c2ce5ba",
  //     })

  //     return Promise.resolve(jsondata)
  //   }
  //   // let assignments1 = main();
  //   // console.log(assignments1);

  //   var p = new Promise(function(resolve, reject) {
  //     setTimeout(function() {
  //       resolve('foo');
  //     }, 300);
  //   });

  //   console.log(p);

  // function getdata(url, params) {
  //   return fetch(url + '?' + new URLSearchParams(params))
  //     .then(function(response) {
  //       return response.json();
  //     })
  //     .then(function(data) {
  //       console.log(data);
  //       //var userid = JSON.parse(data);
  //       //console.log(userid);

  //       return data;
  //     })
  // }

  // async function fetchData(url, params){
  //   let response = await fetch(url + '?' + new URLSearchParams(params));
  //   let data = await response.json();
  //   data = JSON.stringify(data);
  //   data = JSON.parse(data);
  //   return data;
  //  }

  const getData = async (url, params) => {
    fetch(url + "?" + new URLSearchParams(params))
      .then((response) => {
        if (!response.ok) {
          console.log("ok");
        }
        return response.json();
      })
      .then((json) => {
        setData(json)
      })
      .catch((error) => {});
  };

  useEffect(() => {
    getData(api_url, {
      course_id: courseId,
    });
  }, []);

  useEffect(() => {
    if (!courseInfo.id) {
      updateCourseInfo((prevCourseInfo) => ({
        ...prevCourseInfo,
        id: courseId
      }));
    }
    if (!courseInfo.name || !courseInfo.year || !courseInfo.semester || !courseInfo.entryCode) {
      fetch(
        process.env.REACT_APP_API_URL + "/get_course_info?" +
          new URLSearchParams({
            course_id: courseId,
          })
      )
        .then((res) => res.json())
        .then((data) =>
          data.forEach((element) => {
            if (element.id === courseId) {
              updateCourseInfo({
                name: element.name,
                year: element.year,
                semester: element.semester,
                entryCode: element.entryCode,
                id: courseId
              });
              setDescription(element.description)
            }
          })
        );
    }
  }, [courseInfo.id, courseInfo.name, courseInfo.semester, courseId, updateCourseInfo, user_id]);

  const isCourseInfoLoaded = courseInfo.semester && courseInfo.year && courseInfo.entryCode;

  if (!isCourseInfoLoaded) {
    return null;
  }

  return (
    <>
      {/* <div>
        <h1>C S N313E</h1>
        <Space>
          <span>Summer 2022</span>
          <span>Course ID: 394120</span>
        </Space>
      </div> */}
      <PageHeader title={courseInfo.name} subTitle={`${courseInfo.semester} ${courseInfo.year}`}>
        <Descriptions>
          <Descriptions.Item label="Course ID">{courseId}</Descriptions.Item>
        </Descriptions>
      </PageHeader>
      <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
        <h3>DESCRIPTION</h3>
        <Divider style={{ marginTop: 0, marginBottom: "5px" }} />
        <div>
          {description === "" ? (
            <div>
            <span>Edit your course description on the </span>
            <Link to={`/courseSettings/${courseId}`}>Course Settings</Link>
            <span> page.</span>
          </div>
          ) : (
            <span>{description}</span>
          )}
        </div>
      </Card>
      <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
        <h3>THINGS TO DO</h3>
        <Divider style={{ marginTop: 0, marginBottom: "5px" }} />
        <Space direction="vertical">
          {texts.map((item, index) => (
            <TextItem text={item} key={index} />
          ))}
          {/* <div>
            <ExclamationCircleFilled />
            <span> Review and publish grades for </span>
            <Button type='link'>Assignment-0</Button>
            <span>now that you're all done grading.</span>
          </div> */}
        </Space>
      </Card>
      <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
        <Table rowKey="id" columns={columns} dataSource={data} />
        {/*console.log(data)*/}
      </Card>
    </>
  );
}