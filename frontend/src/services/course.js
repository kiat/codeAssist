import service from ".";

export async function getCourseInfo(params) {
  return service("get_course_info", params);
}

export async function getCourseAssignments(params) {
  return service("get_course_assignments", params);
}

export async function createAssignment(params) {
  return service("create_assignment", params, "post");
}

export async function updateCourse(params) {
  return service("update_course", params, "post");
}

export async function deleteCourse(params) {
  return service("delete_course", params, "delete");
}
