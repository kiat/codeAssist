import service from ".";

export async function uploadAssignmentAutograder(params) {
  return service("upload_assignment_autograder", params, "post");
}

export async function uploadSubmission(params) {
  return service("upload_submission", params, "post");
}

