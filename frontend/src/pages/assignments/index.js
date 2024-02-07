import { Card, Descriptions, PageHeader, Table, Button } from "antd";
import axios from "axios";
import { useCallback, useContext, useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { GlobalContext } from "../../App";
import moment from "moment";

import "../../mock/assignment";
import AssignmentModal from "./assignment_modal";

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
  const [isModalOpen, setModalOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [assignmentID, setAssignmentID] = useState("")
  const [assignmentTitle, setAssignmentTitle] = useState("")


  const columns = [
    {
      title: "NAME",
      dataIndex: "name",
      sorter: (a, b) => a.name > b.name,
      render: (text) => (
        <Button type="link" onClick={() => {openModal(text)}}>
          {text}
        </Button>
      )
    },
    {
      title: "STATUS",
      dataIndex: "status",
      render: text => (text === 1 ? "Submitted" : "Not Submitted"),
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

  const openModal = (text) => {
    setModalOpen(true);
    setAssignmentTitle(text)
    const curr_assignment = courseAssignment.find((assignment) => assignment.name === text);
    setAssignmentID(curr_assignment.id)
  }



  const closeModal = () => {
    setModalOpen(false);
  }


  useEffect(() => {
    fetch("http://localhost:5000/get_course_assignments?" +
      new URLSearchParams({
        course_id: courseId
      })
    )
    .then(res => res.json()) // Extract JSON data from the response
    .then(data => {
      //console.log(new Date("" + data[0].published_date + "Z"));
      const convertedData = data;
      for (let i = 0; i < data.length; i++) {
        let thisPublishedDate = convertedData[i].published_date;
        let thisDueDate = convertedData[i].due_date;
        convertedData[i].published_date = (thisPublishedDate) ? thisPublishedDate + "Z" : null;
        convertedData[i].due_date = (thisDueDate) ? thisDueDate + "Z" : null;
      }
      setCourseAssignment(convertedData); // Set the retrieved data in the state
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
        {courseAssignment ? (
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
              onClick: () => {
                const now = Date.now();
                // console.log((
                //   (publishedDate <= now && now <= dueDate) + " " + (dueDate <= now && status === 1)
                //   ));
                if (!(
                  (publishedDate <= now && now <= dueDate) || (dueDate <= now && status === 1)
                  )
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
      <AssignmentModal open={isModalOpen} onCancel={closeModal} assignmentID = {assignmentID} assignmentTitle = {assignmentTitle}/>
    </>
  );
}