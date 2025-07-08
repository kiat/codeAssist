import { Layout, message, Modal } from "antd";
import axios from "axios";
import { BrowserRouter, Route, Routes, useNavigate, useLocation } from "react-router-dom";
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
import RegradeRequests from './components/RegradeRequests';
import AdminDashboard from "./pages/admin/dashboard";
import AdminSidebar from "./components/layout/AdminSidebar";
import { leaveCourse } from "./services/course";
import AdminCourses from "./pages/admin/courses";
import AdminStudents from "./pages/admin/students";
import AdminInstructors from "./pages/admin/instructors";
import AdminInstructorAdd from "./pages/admin/instructors/add";
import AdminInstructorManage from "./pages/admin/instructors/manage"; // <-- Add this import
import AdminAllCourses from "./pages/admin/courses/all";
import AdminStudentManage from "./pages/admin/students/manage";
import AdminStudentAdd from "./pages/admin/students/add";
import AdminCourseManage from "./pages/admin/courses/manage";

const { Content } = Layout;

// Defining initial states as constants to avoid recreating objects on re-renders
const initialUserInfo = { name: "", isStudent: 1, isAdmin: 1 };
const initialCourseInfo = { id: "", name: "", code: "", semester: "", year: "", description: ""};
const initialAssignmentInfo = { id: "", score: "", results: null, code: null };

export const GlobalContext = createContext({
  userInfo: initialUserInfo,
  courseInfo: initialCourseInfo,
  assignmentInfo: initialAssignmentInfo,
  updateCourseInfo: () => {},
  updateUserInfo: () => {},
  updateAssignmentInfo: () => {},
});

function App() {
  const [userInfo, setUserInfo] = useState(() => 
    JSON.parse(localStorage.getItem("userInfo")) || initialUserInfo
  );
  const [courseInfo, setCourseInfo] = useState(() => 
    JSON.parse(localStorage.getItem("courseInfo")) || initialCourseInfo
  );
  const [assignmentInfo, setAssignmentInfo] = useState(initialAssignmentInfo);
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  // Effect for initializing courseInfo from localStorage
  useEffect(() => {
    const storedCourseInfo = localStorage.getItem("courseInfo");
    if (storedCourseInfo) {
      setCourseInfo(JSON.parse(storedCourseInfo));
    }
  }, []);

  // Effect for saving courseInfo to localStorage when it changes
  useEffect(() => {
    localStorage.setItem("courseInfo", JSON.stringify(courseInfo));
  }, [courseInfo]);
  // Callbacks for updating state, using empty dependencies to ensure they don't change
  const updateCourseInfo = useCallback(info => setCourseInfo(info), []);
  const updateUserInfo = useCallback(info => setUserInfo(info), []);
  const updateAssignmentInfo = useCallback(info => setAssignmentInfo(info), []);

  // Redirect to home if not logged in and not on home page
  useEffect(() => {
    if (location.pathname !== "/" && !userInfo.name) {
      navigate("/");
    }
  }, [userInfo, location, navigate]);
  
  const handleLeaveCourse = async (courseId) => {
  Modal.confirm({
    title: "Are you sure you want to leave this course?",
    content: "This action cannot be undone.",
    okText: "Yes, leave",
    cacnelText: "Cancel",
    onOk: async () => {
      try {
        await leaveCourse({ user_id: userInfo.id, course_id: courseId });
        navigate('/dashboard');
      } catch (error) {
        console.error(error);
        message.error("Failed to leave course");
      }
    },
  });
};
  return (
    <GlobalContext.Provider value={{
      userInfo, updateUserInfo,
      courseInfo, updateCourseInfo,
      assignmentInfo, updateAssignmentInfo
    }}>

      <Layout style={{ display: 'flex', height: '100vh', flexDirection: "row" }}>
        {location.pathname === "/" ? null : (
          userInfo?.isAdmin ? (
            <AdminSidebar
              pathname={location.pathname}
              toggleCollapsed={() => setCollapsed(!collapsed)}
            />
          ) : (
            <RootSider
              pathname={location.pathname}
              courseInfo={courseInfo}
              userInfo={userInfo}
              assignmentInfo={assignmentInfo}
              onLeaveCourse={handleLeaveCourse}
            />
          )
        )}
        <Layout style={{ flex: 1, overflow: 'hidden' }}>
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
              <Route path='/admin/dashboard' element={<AdminDashboard/>} />
              <Route path='/admin/courses' element={<AdminCourses />} />
              <Route path='/admin/students' element={<AdminStudents />} />
              <Route path='/admin/instructors' element={<AdminInstructors />} />
              <Route path='/admin/instructors/add' element={<AdminInstructorAdd />} />
              <Route path='/admin/instructors/manage/:instructorId' element={<AdminInstructorManage />} /> {/* <-- Add this route */}
              <Route path='/admin/courses/all' element={<AdminAllCourses />} />
              <Route path='/assignments/:courseId' element={<Assignments />} />
              <Route
                ///reconfiguring to use submissionid for navigation
                path='/assignmentResult/:submissionId'
                //path='/assignmentResult/:assignmentId/:studentId' 
                //old route config
                //path='/assignmentResult/:assignmentId'
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
              {/**
              <Route
                path='/assignment/editOutline/:assignmentId'
                element={<EditOutline />}
              /> 
              */}
              <Route
                path='/assignment/configureAutograder/:assignmentId'
                element={<ConfigureAutograder />}
              />
              {/** 
              <Route
                path='/assignment/createRubric/:assignmentId'
                element={<CreateRubric />}
              />
              */}
              <Route
                path='/assignment/manageSubmissions/:assignmentId'
                element={<ManageSubmissions />}
              />
              {/**
              <Route
                path='/assignment/gradeSubmissions/:assignmentId'
                element={<GradeSubmissions />}
              />
              */}
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
              <Route path="/regradeRequests" element={<RegradeRequests />} />
              <Route path='/admin/students/manage/:studentId' element={<AdminStudentManage />} />
              <Route path='/admin/students/add' element={<AdminStudentAdd />} />
              <Route path='/admin/courses/:courseId/manage' element={<AdminCourseManage />} />
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