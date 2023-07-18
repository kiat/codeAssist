import { Card, Descriptions, PageHeader, Table } from "antd";
import axios from "axios";
import { useCallback, useContext, useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { GlobalContext } from "../../App";
import moment from "moment";

import "../../mock/assignment";

/**
 * course assignment modal
 * @returns
 */
export default function Assignments() {
  const [courseAssignment, setCourseAssignment] = useState([]);
  const urlParams = useParams();
  const {courseId} = urlParams;
  const navigate = useNavigate();
  const { userInfo, courseInfo } = useContext(GlobalContext);
  const location = useLocation();

  const columns = [
    {
      title: "NAME",
      dataIndex: "name",
      sorter: (a, b) => a.name > b.name,
    },
    {
      title: "STATUS",
      dataIndex: "status",
      render: text => (text === 1 ? "Submitted" : "No Submission"),
      sorter: (a, b) => a.status - b.status,
    },
    {
      title: "GRADES",
      dataIndex: "grades",
      render: text => text || "-",
      sorter: (a, b) => a.grades - b.grades,
    },
    {
      title: "RELEASED",
      dataIndex: "published_date",
      render: text => {
        const publishedDate = moment(text).valueOf();
        const formattedDate = moment(text).format("MMM DD [AT] h:mmA").toUpperCase();
        return <span data-timestamp={publishedDate}>{formattedDate}</span>
      },
      sorter: (a, b) => a.released - b.released,
    },
    {
      title: "DUE(CDT)",
      dataIndex: "due_date",
      render: text => {
        const dueDate = moment(text).valueOf();
        const formattedDate = moment(text).format("MMM DD [AT] h:mmA").toUpperCase();
        return <span data-timestamp={dueDate}>{formattedDate}</span>;
      },
      sorter: (a, b) => a.due - b.due,
    },
  ];

  useEffect(() => {
    fetch("http://localhost:5000/get_course_assignments?" +
      new URLSearchParams({
        course_id: courseId
      })
    )
    .then(res => res.json()) // Extract JSON data from the response
    .then(data => {
      setCourseAssignment(data); // Set the retrieved data in the state
  })
    .catch(error => {
      console.error("Error fetching course assignments:", error);
  });
}, []);

  return (
    <>
      <PageHeader
        title={courseInfo.name}
        subTitle={`${courseInfo.semester} ${courseInfo.year}`}
        style={{ borderBottom: "1px solid #f0f0f0" }}
      >
        <Descriptions>
          <Descriptions.Item label='Course ID'>
            {urlParams.courseId}
          </Descriptions.Item>
        </Descriptions>
      </PageHeader>
      {/* <div
        style={{
          display: "flex",
          marginTop: "7px",
        }}
      >
        <div style={{ flex: "1" }}>
          <h3>{courseInfo.code}</h3>
          <h4>{courseInfo.semester}</h4>
          <p>Course ID: {urlParams.courseId}</p>
        </div>
        {userInfo?.isStudent ? null : (
          <div
            style={{
              flexBasis: "150px",
            }}
          >
            <Button icon={<UploadOutlined />} onClick={toggleUploadModalOpen}>
              upload
            </Button>
          </div>
        )}
      </div> */}
      <Card bordered={false}>
        {courseAssignment.some(assignment => assignment.published) ? (
        <Table
          columns={
            columns
            // userInfo?.isStudent
            //   ? columns
            //   : columns.filter(item => item.dataIndex !== "status")
          }
          dataSource={courseAssignment.filter(assignment => assignment.published)}
          rowKey='id'
          onRow={record => {
            const { published_date, id, status, due_date } = record;
            const publishedDate = moment(published_date).valueOf();
            const dueDate = moment(due_date).valueOf();
            return {
              onClick: event => {
                const now = Date.now();
                if (
                  (publishedDate <= now && now <= dueDate) ||
                  (dueDate <= now && status === 1)
                ) {
                  navigate(`/assignmentresult/${id}`);
                }
              },
            };
          }}
        />
        ) : (
          <div>No assignments yet</div>
        )}
      </Card>
    </>
  );
}
