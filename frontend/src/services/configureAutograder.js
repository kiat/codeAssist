import service from ".";

export async function uploadAssignmentAutograder(params) {
  return service("upload_assignment_autograder", params, "post");
}
