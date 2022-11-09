import { Layout } from "antd";
import { BrowserRouter, Route, Routes, useNavigate } from "react-router-dom";
import Home from "./pages/home";
import Dashboard from "./pages/dashboard";
import { createContext, useCallback, useEffect, useState } from "react";
import Assignments from "./pages/assignments";
import AssignmentResult from "./pages/student/result";
import RootSider from "./components/layout/sider";

import "./mock";
import InstructorDashboard from "./pages/instructor/dashboard";
import CourseSettings from "./pages/instructor/courseSettings";
import InstructorAssignments from "./pages/instructor/assignments";
import Enrollment from "./pages/instructor/enrollment";

const { Content } = Layout;

export const GlobalContext = createContext({
  userInfo: { name: "", isStudent: 1 },
  curseInfo: { name: "", code: "" },
  updateCourseInfo: () => {},
  updateUserInfo: () => {},
});

function App() {
  const [courseInfo, setCourseInfo] = useState({ code: "", name: "" });
  const [userInfo, setUserInfo] = useState(
    JSON.parse(localStorage.getItem("userInfo"))
  );
  const navigate = useNavigate();

  const updateCourseInfo = useCallback(info => {
    setCourseInfo(info);
  }, []);

  const updateUserInfo = useCallback(info => {
    setUserInfo(info);
  }, []);

  const pathname = window.location.pathname;

  useEffect(() => {
    if (pathname !== "/" && !userInfo?.name) {
      navigate("/");
    }
  }, [userInfo, courseInfo, pathname, navigate]);

  return (
    <GlobalContext.Provider
      value={{
        courseInfo,
        updateCourseInfo,
        userInfo,
        updateUserInfo,
      }}
    >
      <Layout>
        {pathname === "/" ? null : (
          <RootSider
            pathname={pathname}
            courseInfo={courseInfo}
            userInfo={userInfo}
          />
        )}
        <Layout style={{ height: "100vh" }}>
          <Content
            style={{
              backgroundColor: "#fff",
              // paddingLeft: "20px",
              borderLeft: "1px solid #f0f2f5",
              overflow: "auto",
            }}
          >
            <Routes>
              <Route path='/' element={<Home />} />
              <Route path='/dashboard' element={<Dashboard />} />
              <Route path='/assignments/:courseId' element={<Assignments />} />
              <Route
                path='/assignmentresult/:assignmentId'
                element={<AssignmentResult />}
              />
              <Route
                path='/instructorDashboard'
                element={<InstructorDashboard />}
              />
              <Route
                path='/instructorAssignments'
                element={<InstructorAssignments />}
              />
              <Route path='/courseSettings' element={<CourseSettings />} />
              <Route path='/enrollment' element={<Enrollment />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </GlobalContext.Provider>
  );
}

export default function AppRoute() {
  return (
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
}
