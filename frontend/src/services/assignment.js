import service from ".";

export async function createAssignment(params) {
  return service("create_assginment", params, "post");
}

export async function getAssignment(params) {
  return service("get_assignment", params);
}

export async function updateAssignment(params) {
  return service("update_assignment", params, "post");
}

export async function deleteAssignment(params) {
  return service("delete_assignment", params, "delete");
}
