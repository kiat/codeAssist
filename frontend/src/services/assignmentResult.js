import service from ".";

export async function uploadSubmission(params) {
  return service("upload_submission", params, "post");
}

export async function getLatestSubmission(params) {
  return service("get_latest_submission", params);
}

export async function deleteSubmission(params) {
  return service("delete_submission", params, "delete");
}

export async function getCourseAssignmentLatestSubmission(params) {
  return service("get_course_assignment_latest_submissions", params);
}