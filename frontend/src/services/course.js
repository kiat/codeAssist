import service from ".";

export async function createCourse(params) {
  return service("create_course", params, "post");
}

export async function createEnrollment(params) {
  return service("create_enrollment", params, "post");
}

export async function createEnrollmentCSV(params) {
  return service("create_enrollment_csv", params, "post");
}

export async function deleteAllAssignments(params) {
  return service("delete_all_assignments", params, "delete");
}

export async function deleteCourse(params) {
  return service("delete_course", params, "delete");
}

export async function leaveCourse(params) {
  return service("leave_course", params, "post");
}

export async function enrollCourse(params) {
  return service("enroll_course", params, "post");
}

export async function getCourseAssignments(params) {
  return service("get_course_assignments", params);
}

export async function getCourseEnrollment(params) {
  return service("get_course_enrollment", params);
}

export async function getCourseInfo(params) {
  return service("get_course_info", params);
}

export async function getUserEnrollments(params) {
  return service("get_user_enrollments", params);
}

export async function updateCourse(params) {
  return service("update_course", params, "put");
}

export async function updateRole(params) {
  return service("update_role", params, "post");
}
