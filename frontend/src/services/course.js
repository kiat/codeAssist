import service from ".";

export async function getCourseAssignments(params) {
  return service("get_course_assignments", params);
}

export async function createAssignment(params) {
  return service("create_assignment", params, "post");
}

export async function deleteCourse(params) {
  return service("delete_course", params, "delete");
}

export async function deleteAllAssignments(params) {
  return service("delete_all_assignments", params, "delete");
}

export async function updateCourse(params) {
  return service("update_course", params, "put");
}

export async function getCourseInfo(params) { 
  return service("get_course_info", params);
}