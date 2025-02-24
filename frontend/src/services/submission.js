import service from ".";

export async function uploadSubmission(params) {
  return service("upload_submission", params, "post");
}
