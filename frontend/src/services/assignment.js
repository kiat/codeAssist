import service from ".";

export async function createAssignment(params) {
  return service("create_assignment", params, "post");
}

export async function createExtension(params) {
  return service("create_extension", params, "post");
}

export async function deleteAssignment(assignmentId) {
  const params = new URLSearchParams({ assignment_id: assignmentId });
  return service(`delete_assignment?${params}`, {}, "delete");
}

export async function deleteSubmissions(assignmentId) {
  const params = new URLSearchParams({ assignment_id: assignmentId });
  return service(`delete_submissions?${params}`, {}, "delete");
}

export async function duplicateAssignment(params) {
  return service("duplicate_assignment", params, "post");
}

export async function getAssignment(params) {
  return service("get_assignment", params);
}

export async function getAssignmentAiSettings(assignmentId) {
  return service(`assignments/${assignmentId}/ai-settings`);
}

export async function getExtension(params) {
  return service("get_extension", params);
}

export async function updateAssignment(params) {
  return service("update_assignment", params, "put");
}

export async function updateAssignmentAiSettings(assignmentId, params) {
  return service(`assignments/${assignmentId}/ai-settings`, params, "put");
}
