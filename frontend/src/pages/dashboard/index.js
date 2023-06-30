import { PageHeader } from "antd";
import { useCallback, useContext, useEffect, useState } from "react";
import { GlobalContext } from "../../App";
import SemesterCourses from "./semesterCourses";

import "../../mock/course";
import CourseModal from "./courseModal";
import RelationForm from "./relationForm";
import AddForm from "./addForm";
import {
  createCourse,
  enrollCourse,
  getInstructorCourses,
  getStudentCourses,
} from "../../services/dashboard";

/**
 * dashboard for both student and instructors
 * @returns
 */
export default function Dashboard() {
  const [modalOpen, setModalOpen] = useState(false);
  const [courses, setCourses] = useState({});
  const { userInfo } = useContext(GlobalContext);

  // control course adding modal
  const toggleModalOpen = useCallback(() => {
    setModalOpen(bool => !bool);
  }, []);

  const formatCourse = data => {
    const coursesTemp = { 99999: [] };
    data?.forEach(item => {
      const { semester, year, name, assignments, id } = item;
      if (!coursesTemp[`${year}${semester}`] && semester && year) {
        coursesTemp[`${year}${semester}`] = [];
      }
      // if (!semester && !year && !coursesTemp["noTitle"]) {
      //   coursesTemp["noTitle"] = [];
      // }
      if (semester && year) {
        coursesTemp[`${year}${semester}`].push({ name, assignments, id });
      } else {
        coursesTemp[99999].push({ name, assignments, id });
      }
    });
    return coursesTemp;
  };

  // get course information
  const getCourses = useCallback(() => {
    const { isStudent, id } = userInfo || {};
    if (isStudent) {
      // getInstructorCourses({ id }).then(res => {
      getStudentCourses({ student_id: id }).then(res => {
        setCourses(formatCourse(res.data));
      });
    } else {
      getInstructorCourses({ instructor_id: id }).then(res => {
        setCourses(formatCourse(res.data));
      });
    }
  }, [userInfo]);

  useEffect(() => {
    getCourses();
  }, [getCourses]);

  // action after successfully adding courses
  const afterAddCourse = useCallback(
    values => {
      const { courseName, semester, year, entryCode } = values;
      console.log("values", values);
      if (userInfo?.isStudent && Object.keys(values).length === 1) {
        enrollCourse({student_id: userInfo.id, entryCode: entryCode}).then(res => {
          getCourses();
          toggleModalOpen();
        });
      } else {
        // createCourse({ id: userInfo.id, courseName, ...restValues }).then(res => {
        createCourse({ name: courseName, instructor_id: userInfo.id, semester: semester, year: year, entryCode: entryCode}).then(res => {
          getCourses();
          toggleModalOpen();
        });
      }
      // axios
      //   .post("/api/addCourse", {
      //     isStudent: userInfo?.isStudent,
      //     ...values,
      //   })
      //   .then(res => {
      //     getCourses();
      //     toggleModalOpen();
      //   });
    },
    [getCourses, toggleModalOpen, userInfo?.id]
  );

  // find if the user is an instructor or a student
  return (
    <>
      <PageHeader title='Your Courses' />
      <div
        style={{
          marginLeft: "25px",
        }}
      >
      {userInfo?.isStudent && Object.keys(courses).length === 1 ? (
        <div
          style={{
            border: "1px dashed green",
            width: "230px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            color: "green",
            fontSize: "bold",
            cursor: "pointer",
            height: "125px",
          }}
          onClick={toggleModalOpen}
        >
          + Add a course
        </div>
      ) : null}
        {/* {courses?.map((item, index) => (
          <SemesterCourses
            key={item.semester}
            semesterInfo={item}
            isFirst={index === 0 ? true : false}
            toggleRelationModalOpen={toggleModalOpen}
          />
        ))} */}
        {Object.keys(courses)
          ?.sort((a, b) => b - a)
          .map((item, index) => (
            <SemesterCourses
              key={item}
              yearInfo={item}
              semesterInfo={courses[item]}
              /*isFirst={index === 0 ? true : false}*/
              courseGroup={index}
              numCourses={Object.keys(courses).length - 1}
              toggleRelationModalOpen={toggleModalOpen}
            />
          ))}
      </div>
      <CourseModal
        title='ADD COURSE'
        open={modalOpen}
        onCancel={toggleModalOpen}
      >
        {userInfo?.isStudent ? (
          <RelationForm onFinish={afterAddCourse} onCancel={toggleModalOpen} />
        ) : (
          <AddForm onFinish={afterAddCourse} onCancel={toggleModalOpen} />
        )}
      </CourseModal>
    </>
  );
}