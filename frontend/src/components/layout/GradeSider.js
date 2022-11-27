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

  const [assignmentInfoCurrent, setAssignmentInfoCurrent] = useState();

  const pathname = window.location.pathname;

  useEffect(() => {
    const res = /\/assignment\/\w+\/(\d+)/i.exec(pathname);
    if (res && res[1]) {
      updateAssignmentInfo({
        id: res[1],
        name: "Training-Test-2-Question-1 - Gift Card",
      });
    }
    setAssignmentInfoCurrent({
      courseName: "C S N313E",
      courseId: 21,
      assignmentName: "Training-Test-2-Question-1 - Gift Card",
    });
  }, [pathname, updateAssignmentInfo]);

  return (
    <>
      <Card
        // title='Assignment-11'
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
              {assignmentInfoCurrent?.assignmentName}
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
