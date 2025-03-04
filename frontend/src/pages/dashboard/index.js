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
    height: "138px",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    color: "green",
    fontWeight: "bold", 
    fontSize: "16px", 
    cursor: "pointer",
    boxSizing: "border-box",
    flexShrink: 0, 
    textAlign: "center",
  };

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

  // Function to structure the courses data
  const formatCourses = (coursesArray) => {
    const formattedCourses = {};
    coursesArray.forEach((course) => {
      const { semester, year, name, assignments, id } = course;
      const key = `${year}${semester}`;
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
        <div style={{ display: "flex", flexDirection: "column", gap: "40px", paddingLeft: "30px", width: "100%" }}>
          {Object.keys(courses)
            .sort((a, b) => b.localeCompare(a))
            .map((key, index) => {
              // extract year and semester
              const matches = key.match(/(\d{2,4})(Spring|Summer|Fall|Winter)/);
              const year = matches ? matches[1] : key;
              const semester = matches ? matches[2] : "";

              return (
                <div key={key} style={{ width: "100%" }}>
                  <h3 style={{ fontWeight: "bold", fontSize: "20px", marginBottom: "10px" }}>
                    {semester} {year} 
                  </h3>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "20px", alignItems: "center" }}>
                    {courses[key].map((course, idx) => (
                      <SemesterCourses
                        key={idx}
                        yearInfo={key}
                        semesterInfo={[course]}
                        courseGroup={index}
                        numCourses={Object.keys(courses).length}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
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
