import service from ".";

export async function getCourseEnrollment(params) {
  return service("get_course_enrollment", params);
}

export async function createEnrollment(params) {
  return service("create_enrollment", params, "post");
}

export async function createEnrollmentCSV(params) {
  return service("create_enrollment_csv", params, "post");
}

export async function updateRole(params) {
  return service("update_role", params, "post");
}