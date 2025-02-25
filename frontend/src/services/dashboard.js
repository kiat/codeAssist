import service from ".";

// generalizable to both students and instructors
export async function getUserEnrollments(params) {
  return service("get_user_enrollments", params)
}

export async function createCourse(params) {
  return service("create_course", params, "post");
}

export async function enrollCourse(params) {
  return service("enroll_course", params, "post");
}
