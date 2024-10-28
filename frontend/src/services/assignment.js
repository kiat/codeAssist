import service from ".";

export async function getAssignment(params) {
  return service("get_assignment", params);
}

export async function updateAssignment(params) {
  return service("update_assignment", params, "post");
}

export async function createExtension(params) {
  return service("create_extension", params, "post");
}
