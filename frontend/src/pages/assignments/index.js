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
  const [assignments, setAssignments] = useState([]);
  const urlParams = useParams();
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
      dataIndex: "released",
      render: text => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
      sorter: (a, b) => a.released - b.released,
    },
    {
      title: "DUE(CDT)",
      dataIndex: "due",
      render: text => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
      sorter: (a, b) => a.due - b.due,
    },
  ];

  const getAssignments = useCallback(() => {
    axios.post("/api/getCourse", userInfo).then(res => {
      // updateCourseInfo({
      //   code: res.data.course.code,
      //   name: res.data.course.name,
      //   semester: res.data.course.semester,
      // });
      setAssignments(res.data.course.assignments);
    });
  }, [userInfo]);

  // // update assignment
  // const updateTableData = useCallback(() => {
  //   getAssignments();
  // }, [getAssignments]);

  useEffect(() => {
    getAssignments();
  }, [getAssignments, location.key]);

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
        <Table
          columns={
            columns
            // userInfo?.isStudent
            //   ? columns
            //   : columns.filter(item => item.dataIndex !== "status")
          }
          dataSource={assignments}
          rowKey='id'
          onRow={record => {
            const { released, id, status, due } = record;
            return {
              onClick: event => {
                const now = Date.now();
                if (
                  (released <= now && now <= due) ||
                  (due <= now && status === 1)
                ) {
                  navigate(`/assignmentresult/${id}`);
                }
              },
            };
          }}
        />
      </Card>
    </>
  );
}
