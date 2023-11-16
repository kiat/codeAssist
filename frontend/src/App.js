import { Layout } from "antd";
import { BrowserRouter, Route, Routes, useNavigate } from "react-router-dom";
import Home from "./pages/home";
import Dashboard from "./pages/dashboard";
import { createContext, useCallback, useEffect, useState } from "react";
import Assignments from "./pages/assignments";
import AssignmentResult from "./pages/result";
import RootSider from "./components/layout/sider";

import "./mock";
import InstructorDashboard from "./pages/instructor/dashboard";
import CourseSettings from "./pages/instructor/courseSettings";
import InstructorAssignments from "./pages/instructor/assignments";
import Enrollment from "./pages/instructor/enrollment";
import ReviewGrades from "./pages/reviewGrades";
import EditOutline from "./pages/editOutline";
import ConfigureAutograder from "./pages/configureAutograder";
import CreateRubric from "./pages/createRubric";
import ManageSubmissions from "./pages/manageSubmissions";
import GradeSubmissions from "./pages/gradeSubmissions";
import Extensions from "./pages/extensions";
import AssignmentSettings from "./pages/assignmentSettings";
import EditAccount from "./pages/editAccount";

const { Content } = Layout;

export const GlobalContext = createContext({
  userInfo: { name: "", isStudent: 1 },
  courseInfo: { id: "", name: "", code: "", semester: "", year: "" },
  assignmentInfo: { id: "", score: "", results: null, code: null },
  updateCourseInfo: () => {},
  updateUserInfo: () => {},
  updateAssignmentInfo: () => {},
});

function App() {
  // const [courseInfo, setCourseInfo] = useState({ code: "", name: "", semester: "", year: "" });
  const [courseInfo, setCourseInfo] = useState(
    JSON.parse(localStorage.getItem("courseInfo")) || []
  );
  const [assignmentInfo, setAssignmentInfo] = useState({ name: "" });
  const [userInfo, setUserInfo] = useState(
    JSON.parse(localStorage.getItem("userInfo"))
  );
  const navigate = useNavigate();
  
  useEffect(() => {
    const courseInfoData = window.localStorage.getItem("courseInfo");
    if (!courseInfoData) setCourseInfo(JSON.parse(courseInfoData));
  }, []);

  useEffect(() => {
    window.localStorage.setItem("courseInfo", JSON.stringify(courseInfo));
  }, [courseInfo]);

  const updateCourseInfo = useCallback(info => {
    setCourseInfo(info);
  }, []);

  const updateUserInfo = useCallback(info => {
    setUserInfo(info);
  }, []);

  const updateAssignmentInfo = useCallback(info => {
    setAssignmentInfo(info);
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
        assignmentInfo,
        updateAssignmentInfo,
      }}
    >
      <Layout>
        {pathname === "/" ? null : (
          <RootSider
            pathname={pathname}
            courseInfo={courseInfo}
            userInfo={userInfo}
            assignmentInfo={assignmentInfo}
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
                path='/assignmentResult/:assignmentId'
                element={<AssignmentResult />}
              />
              <Route
                path='/instructorDashboard/:courseId'
                element={<InstructorDashboard />}
              />
              <Route
                path='/instructorAssignments/:courseId'
                element={<InstructorAssignments />}
              />
              <Route
                path='/courseSettings/:courseId'
                element={<CourseSettings />}
              />
              <Route path='/enrollment/:courseId' element={<Enrollment />} />
              <Route
                path='/assignment/reviewGrades/:assignmentId'
                element={<ReviewGrades />}
              />
              <Route
                path='/assignment/editOutline/:assignmentId'
                element={<EditOutline />}
              />
              <Route
                path='/assignment/configureAutograder/:assignmentId'
                element={<ConfigureAutograder />}
              />
              <Route
                path='/assignment/createRubric/:assignmentId'
                element={<CreateRubric />}
              />
              <Route
                path='/assignment/manageSubmissions/:assignmentId'
                element={<ManageSubmissions />}
              />
              <Route
                path='/assignment/gradeSubmissions/:assignmentId'
                element={<GradeSubmissions />}
              />
              <Route
                path='/assignment/extensions/:assignmentId'
                element={<Extensions />}
              />
              <Route
                path='/assignment/assignmentSettings/:assignmentId'
                element={<AssignmentSettings />}
              />
              <Route
                path = '/editAccount/:userId'
                element={<EditAccount />} 
              />
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
