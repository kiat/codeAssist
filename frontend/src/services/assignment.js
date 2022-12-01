import service from ".";

export async function getAssignment(params) {
  return service("get_assignment", params);
}

export async function updateAssignment(params) {
  return service("update_assignment", params, "post");
}
