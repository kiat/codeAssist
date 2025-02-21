import service from ".";

export async function getUserByEmail(params) {
  return service("get_user_by_email", params);
}

export async function getCourseEnrollment(params) {
  return service("get_course_enrollment", params);
}

export async function createEnrollment(params) {
  return service("create_enrollment", params, "post");
}

export async function createEnrollmentCSV(params) {
  return service("create_enrollment_csv", params, "post");
}
