import service from ".";

export async function getCourseAssignments(params) {
  return service("get_course_assignments", params);
}

export async function createAssignment(params) {
  return service("create_assignment", params, "post");
}

export async function deleteCourses(params) {
  return service("delete_course", params, "delete");
}
