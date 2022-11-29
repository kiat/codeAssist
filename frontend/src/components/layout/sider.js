import {
  FileTextOutlined,
  HeatMapOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  PicRightOutlined,
  RedoOutlined,
  SettingOutlined,
  TableOutlined,
  UsergroupAddOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Card, Layout, Popover, Space, Typography } from "antd";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import AccountPopoverContent from "./accountPopoverContent";
import GradeSider from "./GradeSider";
import styles from "./styles.module.css";

export default function RootSider({
  pathname,
  courseInfo,
  userInfo,
  assignmentInfo,
}) {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();

  const toggleCollapsed = () => {
    setCollapsed(!collapsed);
  };

  return (
    <Layout.Sider
      collapsible
      collapsed={collapsed}
      trigger={null}
      theme='light'
      style={{
        height: "calc(100vh - 40px)",
        paddingTop: "10px",
        overflow: "auto",
      }}
    >
      {collapsed ? (
        <>
          <div
            style={{
              fontWeight: "bold",
              color: "#1ca0a0",
              paddingLeft: "20px",
            }}
          >
            <div
              style={{
                marginBottom: "20px",
              }}
            >
              <MenuUnfoldOutlined onClick={toggleCollapsed} />
            </div>
            {/\/dashboard/.test(pathname) ? null : (
              <>
                <div
                  style={{
                    marginBottom: "20px",
                  }}
                >
                  <PicRightOutlined />
                </div>
                {/* <div>
                  <RedoOutlined />
                </div> */}
              </>
            )}
          </div>
          <div
            style={{
              backgroundColor: "#1ca0a0",
              position: "fixed",
              bottom: "0",
              width: "80px",
              lineHeight: "40px",
              paddingLeft: "20px",
            }}
          >
            <UserOutlined />
          </div>
        </>
      ) : (
        <>
          <div
            style={
              {
                // paddingLeft: "20px",
              }
            }
          >
            <Typography.Title
              level={4}
              style={{
                fontWeight: "bold",
                color: "#1890ff",
                marginLeft: "15px",
                marginTop: "12px",
              }}
            >
              <HeatMapOutlined />
              {/* <span> GRADING </span> */}
              <Link to='/dashboard'> GRADING </Link>
              <MenuFoldOutlined
                onClick={toggleCollapsed}
                style={{
                  marginLeft: "30px",
                }}
              />
            </Typography.Title>

            {/\/assignment\//.test(pathname) ||
            (/\/assignmentResult\//i.test(pathname) && !userInfo?.isStudent) ? (
              <GradeSider />
            ) : /dashboard/.test(pathname) ? (
              <Card
                title={
                  <Typography.Title level={5} style={{ fontWeight: "bold" }}>
                    Your Courses
                  </Typography.Title>
                }
                bordered={false}
                size='small'
              >
                <span>
                  Welcome to grading! Click on one of your courses to the right,
                  or on the Account menu below.
                </span>
              </Card>
            ) : (
              <>
                <Card
                  bordered={false}
                  title={
                    <>
                      <Typography.Title
                        level={4}
                        style={{ fontWeight: "bold" }}
                      >
                        C S N313E
                      </Typography.Title>
                      <div style={{ whiteSpace: "normal" }}>
                        Su22 - ELEMENTS OF SOFTWARE DESIGN-WB(86439)
                      </div>
                    </>
                  }
                  size='small'
                >
                  <Space
                    direction='vertical'
                    // style={{
                    //   marginLeft: "10px",
                    // }}
                    className={styles.iconText}
                  >
                    <Link
                      to={
                        userInfo?.isStudent
                          ? // ? "/dashboard/"
                            `/assignments/${courseInfo.id}`
                          : // "/assignments/" + courseInfo.id
                            `/instructorDashboard/${courseInfo.id}`
                      }
                      className={
                        /dashboard/i.test(pathname) ||
                        /\/assignments\//i.test(pathname)
                          ? ""
                          : styles.linkText
                      }
                    >
                      <TableOutlined />
                      <span> Dashboard</span>
                    </Link>
                    {userInfo?.isStudent ? (
                      <div
                        style={{
                          cursor: "pointer",
                        }}
                        onClick={() => {
                          navigate();
                        }}
                      >
                        <RedoOutlined />
                        <span> Regrade Requests</span>
                      </div>
                    ) : (
                      <>
                        <Link
                          to={`/instructorAssignments/${courseInfo.id}`}
                          className={
                            // pathname === "/instructorAssignments"
                            /\/instructorAssignments\//i.test(pathname)
                              ? ""
                              : styles.linkText
                          }
                        >
                          <FileTextOutlined />
                          <span> Assignments</span>
                        </Link>
                        <Link
                          to={`/enrollment/${courseInfo.id}`}
                          className={
                            // pathname === "/enrollment"
                            /\/enrollment\//i.test(pathname)
                              ? ""
                              : styles.linkText
                          }
                        >
                          <UsergroupAddOutlined />
                          <span> Enrollment</span>
                        </Link>
                        <Link
                          // to='/courseSettings'
                          to={`/courseSettings/${courseInfo.id}`}
                          className={
                            // pathname === "/courseSettings"
                            /\/courseSettings\//i.test(pathname)
                              ? ""
                              : styles.linkText
                          }
                        >
                          <SettingOutlined />
                          <span> Course Settings</span>
                        </Link>
                      </>
                    )}
                  </Space>
                </Card>
                <Card
                  title={userInfo?.isStudent ? "STUDENT" : "INSTRUCTOR"}
                  size='small'
                  bordered={false}
                >
                  <div
                    className={styles.iconText}
                    // style={{
                    //   marginLeft: "10px",
                    // }}
                  >
                    <UserOutlined />
                    <span> {userInfo?.name}</span>
                  </div>
                </Card>
                <Card title='COURSE ACTIONS' size='small' bordered={false}>
                  <div className={styles.iconText}>
                    <Link to='/dashboard' className={styles.linkText}>
                      <LogoutOutlined />
                      <span> Leave Course</span>
                    </Link>
                  </div>
                </Card>
              </>
            )}
          </div>
          <Popover content={<AccountPopoverContent />} placement='topLeft'>
            <div
              style={{
                backgroundColor: "#1890ff",
                position: "fixed",
                width: "200px",
                bottom: 0,
                lineHeight: "40px",
                color: "white",
                fontWeight: "bold",
                paddingLeft: "20px",
              }}
            >
              <UserOutlined />
              <span> Account</span>
            </div>
          </Popover>
        </>
      )}
    </Layout.Sider>
  );
}
