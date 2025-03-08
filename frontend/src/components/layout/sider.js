import { Layout } from "antd";
import { useState, useContext, useEffect } from "react";
import { GlobalContext } from "../../App";
import CollapsedSidebar from "./CollapsedSidebar";
import ExpandedSidebar from "./ExpandedSidebar";
import { getCourseInfo } from "../../services/course";

export default function RootSider({ pathname, courseInfo, userInfo, assignmentInfo }) {
  const [collapsed, setCollapsed] = useState(false);
  const { updateCourseInfo } = useContext(GlobalContext);
  
  const toggleCollapsed = () => {
    setCollapsed(!collapsed);
  };

  useEffect(() => {
    const fetchCourseInfo = async() => {
      if (courseInfo.id && (!courseInfo.name || !courseInfo.year || !courseInfo.semester || !courseInfo.entryCode)) {
        try {
          const response = await getCourseInfo({course_id: courseInfo.id});
          const data = response.data;
      
          data.forEach((element) => {
            if (element.id === courseInfo.id) {
              updateCourseInfo({
                id: courseInfo.id,
                name: element.name,
                year: element.year,
                semester: element.semester,
                entryCode: element.entryCode,
              });
            }
          });
        } catch (error) {
          console.error("Error fetching course info:", error);
        }
      }
    };
    fetchCourseInfo();
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
