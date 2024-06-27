import { Layout } from "antd";
import { useState, useContext, useEffect } from "react";
import { GlobalContext } from "../../App";
import CollapsedSidebar from "./CollapsedSidebar";
import ExpandedSidebar from "./ExpandedSidebar";
import { getCourseInfo } from "../../services/course"

export default function RootSider({ pathname, courseInfo, userInfo, assignmentInfo }) {
  const [collapsed, setCollapsed] = useState(false);
  const { updateCourseInfo } = useContext(GlobalContext);
  
  const toggleCollapsed = () => {
    setCollapsed(!collapsed);
  };

  useEffect(() => {
    if (courseInfo.id && (!courseInfo.name || !courseInfo.year || !courseInfo.semester || !courseInfo.entryCode)) {
      // fetch(process.env.REACT_APP_API_URL + "/get_course_info?" + new URLSearchParams({ course_id: courseInfo.id }))
      //   .then((res) => res.json())
      //   .then((data) => {
      //     data.forEach((element) => {
      //       if (element.id === courseInfo.id) {
      //         updateCourseInfo({
      //           id: courseInfo.id,
      //           name: element.name,
      //           year: element.year,
      //           semester: element.semester,
      //           entryCode: element.entryCode
      //         });
      //       }
      //     });
      //   });
      console.log("grabbing course info at:", courseInfo);
      getCourseInfo({ course_id: courseInfo.id }); // TODO: still needs testing
    }
  }, [courseInfo, updateCourseInfo]);

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
      {collapsed ? 
        <CollapsedSidebar toggleCollapsed={toggleCollapsed} pathname={pathname} /> : 
        <ExpandedSidebar courseInfo={courseInfo} userInfo={userInfo} pathname={pathname} toggleCollapsed={toggleCollapsed} />
      }
    </Layout.Sider>
  );
}
