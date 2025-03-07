import { PageHeader, message } from "antd";
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

export default function Dashboard() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [courses, setCourses] = useState({});
  const { userInfo } = useContext(GlobalContext);

  const semesterOrder = { Spring: 1, Summer: 2, Fall: 3, Winter: 4 };
  
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
      const key = `${year}-${semester}`;
      if (!formattedCourses[key]) {
        formattedCourses[key] = [];
      }
      formattedCourses[key].push({ name, assignments, id });
    });

    return Object.keys(formattedCourses)
      .sort((a, b) => {
        const [yearA, semesterA] = a.split("-");
        const [yearB, semesterB] = b.split("-");
        return (
          parseInt(yearA) - parseInt(yearB) || // Sort years in ascending order
          (semesterOrder[semesterA] || 99) - (semesterOrder[semesterB] || 99) // Sort semesters chronologically
        );
      })
      .reduce((sortedCourses, key) => {
        sortedCourses[key] = formattedCourses[key];
        return sortedCourses;
      }, {});
  };

  // Fetches courses for the user
  const fetchCourses = useCallback(() => {
    if (!userInfo?.id) return; // Ensure user info is available

    getUserEnrollments({ user_id: userInfo.id })
      .then((response) => {
        if (response && Array.isArray(response.data)) {
          setCourses(formatCourses(response.data));
        } else {
          console.error("Expected an array, received:", response);
          setCourses({});
        }
      })
      .catch((error) => {
        console.error("Error fetching courses:", error);
      });
  }, [userInfo]);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  // Handles adding a course
  const handleAddCourse = useCallback(
    (values) => {
      const isStudent = userInfo?.isStudent;
      const addCourseFunction = isStudent ? enrollCourse : createCourse;
      const params = isStudent
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
        {/* Render semester groups */}
        {Object.keys(courses).map((key, index) => {
          const [year, semester] = key.split("-");

          return (
            <SemesterCourses
              key={key}
              yearInfo={year} // Year as a string
              semesterInfo={semester} // Semester as a string
              courses={courses[key]} // Pass the list of courses
              courseGroup={index}
              numCourses={Object.keys(courses).length}
            />
          );
        })}

        {/* Add Course Button */}
        <div style={courseContainerStyle}>
          <div style={addCourseButtonStyle} onClick={toggleModal}>
            + Add a course
          </div>
        </div>
      </div>

      {/* Add Course Modal */}
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

