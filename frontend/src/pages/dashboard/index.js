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
} from "../../services/course";
import { Button, message, Form, Modal, Upload } from "antd";

export default function Dashboard() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [courses, setCourses] = useState({});
  const { userInfo } = useContext(GlobalContext);

  // Inline styles for the component
  const addCourseButtonStyle = {
    border: "1px dashed green",
    width: "230px",
    height: "125px",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    color: "green",
    fontSize: "bold",
    cursor: "pointer",
    boxSizing: "border-box",
    padding: "10px",
    margin: "0 10px 20px 0",
    flex: "0 0 auto",
  };

  const courseContainerStyle = {
    paddingTop: "30px",
  };

  const courseHeaderStyle = {
    marginLeft: "25px",
    display: "flex",
    flexWrap: "wrap",
    gap: "20px",
    alignItems: "flex-start",
  };

  // Toggle the visibility of the course modal
  const toggleModal = useCallback(() => {
    setIsModalOpen((prevState) => !prevState);
  }, []);

  // Function to structure the courses data
  const formatCourses = (coursesArray) => {
    const formattedCourses = {};
    coursesArray.forEach((course) => {
      const { semester, year, name, assignments, id } = course;
      const key = `${year}${semester}`; // Assuming year and semester are always present
      if (!formattedCourses[key]) {
        formattedCourses[key] = [];
      }
      formattedCourses[key].push({ name, assignments, id });
    });
    return formattedCourses;
  };

  // Function to fetch courses based on the user's role
  const fetchCourses = useCallback(() => {
    const fetchFunction = getUserEnrollments;
    const params = {user_id: userInfo.id};
    fetchFunction(params)
      .then((response) => {
        if (response && Array.isArray(response.data)) {
          const formatted = formatCourses(response.data);
          setCourses(formatted);
        } else {
          console.error("Expected an array, received:", response);
          setCourses({});
        }
      })
      .catch((error) => {
        console.error("Error fetching courses:", error);
      });
  }, [userInfo]);

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
        {Object.keys(courses)
          .sort((a, b) => b.localeCompare(a))
          .map((key, index) => (
            <SemesterCourses
              key={key}
              courses={{ [key]: courses[key] }} // <-- rename and wrap correctly
              toggleModal={toggleModal}
            />
          ))}
        <div style={courseContainerStyle}>
          <div style={addCourseButtonStyle} onClick={toggleModal}>
            + Add a course
          </div>
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