import IMock from "./common";
import { COURSES, SUCCESS } from "./constant";

const courses = COURSES;

IMock(
  "/api/getCourses",
  function (params) {
    return {
      ...SUCCESS,
      data: courses,
    };
  },
  "post"
);

IMock(
  "/api/addCourse",
  function (params) {
    const { isStudent, entryCode, courseName } = params;
    courses[0].courses.push({
      id: Math.random(),
      code: isStudent ? "T" + Math.random() : entryCode,
      name: isStudent ? "TEST " + Math.random() : courseName,
      assignmentCount: parseInt(Math.random() * 10),
    });
    return {
      ...SUCCESS,
      data: courses,
    };
  },
  "post"
);
