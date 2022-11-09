import { PageHeader } from "antd";
import axios from "axios";
import { useCallback, useContext, useEffect, useState } from "react";
import { GlobalContext } from "../../App";
import SemesterCourses from "./semesterCourses";

import "../../mock/course";
import CourseModal from "./courseModal";
import RelationForm from "./relationForm";
import AddForm from "./addForm";

/**
 * dashboard
 * for both instructor and student
 * @returns
 */
export default function Dashboard() {
  const [modalOpen, setModalOpen] = useState(false);
  const [courses, setCourses] = useState([]);
  const { userInfo } = useContext(GlobalContext);

  //add course windows
  const toggleModalOpen = useCallback(() => {
    setModalOpen(bool => !bool);
  }, []);

  // get course information
  const getCourses = useCallback(() => {
    axios
      .post("/api/getCourses", { isStudent: userInfo?.isStudent })
      .then(res => {
        setCourses(res.data.data);
      });
  }, [userInfo?.isStudent]);

  useEffect(() => {
    getCourses();
  }, [getCourses]);

  // after add a course action
  const afterAddCourse = useCallback(
    values => {
      axios
        .post("/api/addCourse", {
          isStudent: userInfo?.isStudent,
          ...values,
        })
        .then(res => {
          getCourses();
          toggleModalOpen();
        });
    },
    [getCourses, toggleModalOpen, userInfo?.isStudent]
  );

  // identify student or instructor
  return (
    <>
      <PageHeader title='Your Courses' />
      <div
        style={{
          marginLeft: "25px",
        }}
      >
        {courses.map((item, index) => (
          <SemesterCourses
            key={item.semester}
            semesterInfo={item}
            isFirst={index === 0 ? true : false}
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
