import { PageHeader } from "antd";
import { useCallback, useContext, useEffect, useState } from "react";
import { GlobalContext } from "../../App";
import SemesterCourses from "./semesterCourses";
import CourseModal from "./courseModal";
import RelationForm from "./relationForm";
import AddForm from "./addForm";
import {
  createCourse,
  enrollCourse,
  getUserEnrollments,
  getCourseAssignments,
} from "../../services/course";
import {  message } from "antd";

export default function Dashboard() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [courses, setCourses] = useState({});
  const { userInfo } = useContext(GlobalContext);

  // Inline styles for the component

  const courseHeaderStyle = {
    display: "flex",
    flexWrap: "wrap",
    gap: "20px",
    alignItems: "flex-start",
    justifyContent: "flex-start", 
    width: "100%", 
    paddingLeft: "30px"
  };

  // Toggle the visibility of the course modal
  const toggleModal = useCallback(() => {
    setIsModalOpen((prevState) => !prevState);
  }, []);

  // Function to fetch assignments count for each course
  const getAssignmentsCount = async (courseId) => {
    try {
      const res = await getCourseAssignments({ course_id: courseId });
      return res.data.length;
    } catch (error) {
      console.error(`Error fetching assignments for course ${courseId}:`, error);
      return 0; 
    }
  };

  // Function to structure the courses data
  const formatCourses = useCallback (async (coursesArray) => {
    const formattedCourses = {};

    for (const course of coursesArray) {
      const { semester, year, name, description, id } = course;
      const key = `${year}${semester}`;

      // Fetch assignments count for each course
      const assignmentsCount = await getAssignmentsCount(id);

      if (!formattedCourses[key]) {
        formattedCourses[key] = [];
      }

      formattedCourses[key].push({ name, description, assignments: assignmentsCount, id });
    }

    return formattedCourses;
  }, []);

  // Function to fetch courses and assignments
  const fetchCourses = useCallback(() => {
    const fetchFunction = getUserEnrollments;
    const params = { user_id: userInfo.id };

    fetchFunction(params)
      .then(async (response) => {
        if (response && Array.isArray(response.data)) {
          const formatted = await formatCourses(response.data);
          setCourses(formatted);
        } else {
          console.error("Expected an array, received:", response);
          setCourses({});
        }
      })
      .catch((error) => {
        console.error("Error fetching courses:", error);
      });
  }, [userInfo, formatCourses]);

  // Fetch courses on mount and when userInfo changes
  useEffect(() => {
    fetchCourses();
  }, [fetchCourses, userInfo]);

  // Fetch courses on mount and when userInfo changes
  useEffect(() => {
    fetchCourses();
  }, [fetchCourses, userInfo]);

  // Function to handle adding a new course
  const handleAddCourse = useCallback(
    (values) => {
      const addCourseFunction = userInfo?.isStudent
        ? enrollCourse
        : createCourse;
      const params = userInfo?.isStudent
        ? { user_id: userInfo.id, entryCode: values.entryCode }
        : {
            name: values.courseName,
            instructor_id: userInfo.id,
            semester: values.semester,
            year: values.year,
            entryCode: values.entryCode,
            allowEntryCode: values.allowEntryCode,
          };
      
      addCourseFunction(params)
        .then(() => {
          message.success("Successfully added course");
          toggleModal();
          fetchCourses();
        })
        .catch((error) => {
          console.error("Error adding course:", error);
        });
    },
    [fetchCourses, toggleModal, userInfo]
  );

  return (
    <>
      <PageHeader title="Your Courses" />
      <div style={courseHeaderStyle}>
        <div style={{ display: "flex", flexDirection: "column", gap: "40px", width: "100%" }}>
            <SemesterCourses courses={courses} toggleModal={toggleModal}/>
        </div>
      </div>

      <CourseModal title="ADD COURSE" open={isModalOpen} onCancel={toggleModal}>
        {userInfo?.isStudent ? (
          <RelationForm onFinish={handleAddCourse} onCancel={toggleModal} />
        ) : (
          <AddForm onFinish={handleAddCourse} onCancel={toggleModal} />
        )}
      </CourseModal>
    </>
  );
}
