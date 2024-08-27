import service from ".";

export async function getCourseEnrollment(params) {
  return service("get_course_enrollment", params);
}

export async function createEnrollment(params) {
  return service("create_enrollment", params, "post");  
}

export async function createEnrollmentBulk(params) {
  return service("create_enrollment_bulk", params, "post");
}

export async function createTA(params) {
  return service("create_ta_enrollment", params, "post");
}

export async function deleteEnrollment(params) {
  return service("delete_enrollment", params, "delete");
}