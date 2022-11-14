import { Card, Descriptions, PageHeader, Table } from "antd";
import axios from "axios";
import { useCallback, useContext, useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { GlobalContext } from "../../App";
import UploadModal from "../../components/UploadModal";

import "../../mock/assignment";
import { columns } from "./constant";

/**
 * assignment modal
 * @returns
 */
export default function Assignments() {
  const [assignments, setAssignments] = useState([]);
  const [uploadModalOpen, setUploadModal] = useState(false);
  const urlParams = useParams();
  const navigate = useNavigate();
  const { userInfo, courseInfo, updateCourseInfo } = useContext(GlobalContext);
  const location = useLocation();

  // assignment file uploading windows modal
  const toggleUploadModalOpen = useCallback(() => {
    setUploadModal(t => !t);
  }, []);

  const getAssignments = useCallback(() => {
    axios.post("/api/getCourse", userInfo).then(res => {
      updateCourseInfo({
        code: res.data.course.code,
        name: res.data.course.name,
        semester: res.data.course.semester,
      });
      setAssignments(res.data.course.assignments);
    });
  }, [updateCourseInfo, userInfo]);

  // update assignment
  const updateTableData = useCallback(() => {
    getAssignments();
  }, [getAssignments]);

  useEffect(() => {
    getAssignments();
  }, [getAssignments, location.key]);

  return (
    <>
      <PageHeader
        title={courseInfo.code}
        subTitle={courseInfo.semester}
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
            userInfo?.isStudent
              ? columns
              : columns.filter(item => item.dataIndex !== "status")
          }
          dataSource={assignments}
          rowKey='id'
          onRow={
            userInfo?.isStudent
              ? record => {
                  const { released, id, status, due } = record;
                  return {
                    onClick: event => {
                      const now = Date.now();
                      if (released < now && now < due) {
                        if (status === 1) {
                          navigate(`/assignmentresult/${id}`);
                        } else {
                          toggleUploadModalOpen();
                        }
                      }
                    },
                  };
                }
              : null
          }
        />
      </Card>
      <UploadModal
        title='UPLOAD'
        url='/api/uploadFile'
        open={uploadModalOpen}
        onCancel={toggleUploadModalOpen}
        afterUpdate={updateTableData}
      />
    </>
  );
}
