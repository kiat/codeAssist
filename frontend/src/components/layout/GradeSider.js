import {
  CheckCircleFilled,
  ClockCircleOutlined,
  LeftOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { Card, Divider, Space, Typography } from "antd";
import { useState, useEffect, useContext } from "react";
import { Link } from "react-router-dom";
import { GlobalContext } from "../../App";
import styles from "./styles.module.css";

export default () => {
  const { assignmentInfo, updateAssignmentInfo } = useContext(GlobalContext);
  const { courseInfo, updateCourseInfo } = useContext(GlobalContext);
  const [assignmentInfoCurrent, setAssignmentInfoCurrent] = useState();

  const pathname = window.location.pathname;
  const res = /\/assignment\/\w+\/([A-Za-z0-9\-]+)/.exec(pathname);
  const assignmentId = res ? res[1] : null;
  useEffect(() => {
    setAssignmentInfoCurrent({
      courseName: courseInfo.name,
      courseId: courseInfo.id,
    });
  }, [pathname, updateAssignmentInfo]);

  useEffect(() => {
    if (!assignmentInfo.id) {
      updateAssignmentInfo((prevAssignmentInfo) => ({
        ...prevAssignmentInfo,
        id: assignmentId
      }));
    }
    fetch(process.env.REACT_APP_API_URL + "/get_course_assignments?" +
    new URLSearchParams({
      course_id: courseInfo.id,
    })
    )
    .then((res) => res.json())
        .then((data) =>
          data.forEach((element) => {
            if (element.id === assignmentId) {
              updateAssignmentInfo({
                id: element.id,
                name: element.name,
              });
            }
          })
        );
    }, [assignmentInfo.id, assignmentInfo.name, updateAssignmentInfo])
  
  return (
    <>
      <Card
        title={
          <>
            <Link
              to={`/instructorDashboard/${assignmentInfoCurrent?.courseId}`}
              className={styles.backIconText}
            >
              <LeftOutlined />
              <span> Back to {assignmentInfoCurrent?.courseName}</span>
            </Link>
            <Typography.Title
              level={4}
              style={{ fontWeight: "bold" }}
              ellipsis={true}
            >
              {assignmentInfo?.name}
            </Typography.Title>
          </>
        }
        bordered={false}
        size='small'
      >
        <Space direction='vertical' className={styles.iconText}>
          <Link
            to={`/assignment/editOutline/${assignmentInfo?.id}`}
            className={/editOutline/i.test(pathname) ? "" : styles.linkText}
          >
            <CheckCircleFilled />
            <span> Edit Outline</span>
          </Link>
          <Link
            to={`/assignment/configureAutograder/${assignmentInfo?.id}`}
            className={
              /configureAutograder/i.test(pathname) ? "" : styles.linkText
            }
          >
            <CheckCircleFilled />
            <span> Configure Autograder</span>
          </Link>
          <Link
            to={`/assignment/createRubric/${assignmentInfo?.id}`}
            className={/createRubric/i.test(pathname) ? "" : styles.linkText}
          >
            <CheckCircleFilled />
            <span> Create Rubric</span>
          </Link>
          <Link
            to={`/assignment/manageSubmissions/${assignmentInfo?.id}`}
            className={
              /manageSubmissions/i.test(pathname) ? "" : styles.linkText
            }
          >
            <CheckCircleFilled />
            <span> Manage Submissions</span>
          </Link>
          <Link
            to={`/assignment/gradeSubmissions/${assignmentInfo?.id}`}
            className={
              /gradeSubmissions/i.test(pathname) ? "" : styles.linkText
            }
          >
            <CheckCircleFilled />
            <span> Grade Submissions</span>
          </Link>
          <Link
            to={`/assignment/reviewGrades/${assignmentInfo.id}`}
            className={/reviewGrades/i.test(pathname) ? "" : styles.linkText}
          >
            <CheckCircleFilled />
            <span> Review Grades</span>
          </Link>
        </Space>
      </Card>
      <Divider />
      <Card bordered={false} size='small'>
        <Space direction='vertical' className={styles.iconText}>
          <Link
            to={`/assignment/extensions/${assignmentInfo.id}`}
            className={/extensions/i.test(pathname) ? "" : styles.linkText}
          >
            <ClockCircleOutlined />
            <span> Extensions</span>
          </Link>
          <Link
            to={`/assignment/assignmentSettings/${assignmentInfo.id}`}
            className={
              /assignmentSettings/i.test(pathname) ? "" : styles.linkText
            }
          >
            <SettingOutlined />
            <span> Assignment Settings</span>
          </Link>
        </Space>
      </Card>
    </>
  );
};
