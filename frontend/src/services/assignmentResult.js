import service from ".";

export async function uploadSubmission(params) {
  return service("upload_submission", params, "post");
}

export async function getLatestSubmission(params) {
  return service("get_latest_submission", params);
}
