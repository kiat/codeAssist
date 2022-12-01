import service from ".";

export async function getInstructorCourses(params) {
  return service("get_instructor_courses", params);
}

export async function getStudentCourses(params) {
  return service("get_student_enrollments", params);
}

export async function createCourse(params) {
  return service("create_course", params, "post");
}
