import React, { useContext } from 'react';
import { Link } from 'react-router-dom';
import { Card, Typography, Space, Popover } from 'antd';
import { MenuFoldOutlined, TableOutlined, FileTextOutlined, UsergroupAddOutlined, SettingOutlined, UserOutlined, LogoutOutlined, RedoOutlined, RobotOutlined } from '@ant-design/icons';
import AccountPopoverContent from './accountPopoverContent';
import GradeSider from './GradeSider';
import styles from './styles.module.css';
import { GlobalContext } from '../../App';

const ROLE_LABELS = {
  instructor: "INSTRUCTOR",
  ta: "TEACHING ASSISTANT",
  student: "STUDENT",
};

function ExpandedSidebar({ courseInfo, userInfo, pathname, toggleCollapsed, handleLeaveCourse }) {
  const { courseRole } = useContext(GlobalContext);

  // Fall back to global account role while courseRole is being fetched from the server.
  // This prevents instructors from briefly seeing the student view on load.
  const effectiveRole = courseRole || (userInfo?.isStudent ? "student" : "instructor");

  const isStudent = effectiveRole === "student";
  const isTA = effectiveRole === "ta";
  const isInstructor = effectiveRole === "instructor";
  const isCourseStaff = isTA || isInstructor;

  const roleLabel = ROLE_LABELS[courseRole] || (userInfo?.role?.toUpperCase() ?? "");

  return (
    <>
      <div>
        <Typography.Title
          level={4}
          style={{
            fontWeight: 'bold',
            color: '#1890ff',
            marginLeft: '15px',
            marginTop: '12px',
          }}
        >
          <Link to='/dashboard'> Feedback </Link>
          <MenuFoldOutlined onClick={toggleCollapsed} style={{ marginLeft: '30px' }} />
        </Typography.Title>

        {/\/assignment\//.test(pathname) || (/\/assignmentResult\//i.test(pathname) && isCourseStaff) ? (
          <GradeSider />
        ) : /dashboard/.test(pathname) ? (
          <Card title={<Typography.Title level={5} style={{ fontWeight: 'bold' }}>Your Courses</Typography.Title>} bordered={false} size='small'>
            <span>Welcome to grading! Click on one of your courses to the right, or on the Account menu below.</span>
          </Card>
        ) : (
          <>
            <Card
              bordered={false}
              title={
                <>
                  <Typography.Title level={4} style={{ fontWeight: 'bold' }}>{courseInfo.name}</Typography.Title>
                  <div style={{ whiteSpace: 'normal' }}>{courseInfo.semester} {courseInfo.year} - {courseInfo.entryCode}</div>
                </>
              }
              size='small'
            >
              <Space direction='vertical' className={styles.iconText}>
                <Link to={isStudent ? `/assignments/${courseInfo.id}` : `/instructorDashboard/${courseInfo.id}`} className={/instructorDashboard/i.test(pathname) || /assignments/i.test(pathname) ? "" : styles.linkText}>
                  <TableOutlined />
                  <span> Dashboard</span>
                </Link>
                <Link to={'/regradeRequests'} className={/regradeRequests/i.test(pathname) ? "" : styles.linkText}>
                  <RedoOutlined />
                  <span> Regrade Requests</span>
                </Link>
                {isCourseStaff && (
                  <>
                    <Link to={`/instructorAssignments/${courseInfo.id}`} className={/instructorAssignments/i.test(pathname) ? "" : styles.linkText}>
                      <FileTextOutlined />
                      <span> Assignments</span>
                    </Link>
                    <Link to={`/enrollment/${courseInfo.id}`} className={/enrollment/i.test(pathname) ? "" : styles.linkText}>
                      <UsergroupAddOutlined />
                      <span> Enrollment</span>
                    </Link>
                  </>
                )}
                {isInstructor && (
                  <>
                    <Link to={`/courseSettings/${courseInfo.id}`} className={/courseSettings/i.test(pathname) ? "" : styles.linkText}>
                      <SettingOutlined />
                      <span> Course Settings</span>
                    </Link>
                    <Link to={`/aiSettings/${courseInfo.id}`} className={/aiSettings/i.test(pathname) ? "" : styles.linkText}>
                      <RobotOutlined />
                      <span> AI Settings</span>
                    </Link>
                  </>
                )}
              </Space>
            </Card>
            <Card title={roleLabel} size='small' bordered={false}>
              <div className={styles.iconText}>
                <UserOutlined />
                <span> {userInfo?.name}</span>
              </div>
            </Card>
            {isStudent && typeof handleLeaveCourse === "function" && courseInfo?.id && (
              <Card title='COURSE ACTIONS' size='small' bordered={false}>
                <div
                  className={`${styles.iconText} ${styles.leaveCourseContainer}`}
                  onClick={() => handleLeaveCourse(courseInfo.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <LogoutOutlined className={styles.leaveCourseIcon} />
                  <span className={`${styles.linkText} ${styles.leaveCourse}`}> Leave Course</span>
                </div>
              </Card>
            )}
          </>
        )}
      </div>
      <Popover content={<AccountPopoverContent />} placement='topLeft'>
        <div
          style={{
            backgroundColor: '#1890ff',
            position: 'fixed',
            width: '200px',
            bottom: 0,
            lineHeight: '40px',
            color: 'white',
            fontWeight: 'bold',
            paddingLeft: '20px',
          }}
        >
          <UserOutlined />
          <span> Account</span>
        </div>
      </Popover>
    </>
  );
}

export default ExpandedSidebar;
