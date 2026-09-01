import service from ".";

export async function uploadAssignmentAutograder(params) {
  return service("upload_assignment_autograder", params, "post");
}

export async function uploadSubmission(params) {
  return service("upload_submission", params, "post");
}

// Code Editor endpoints
export async function saveCodeDraft(params) {
  return service("save_code_draft", params, "post");
}

export async function getCodeDrafts(params) {
  return service("get_code_drafts", params);
}

export async function getLatestDraft(params) {
  return service("get_latest_draft", params);
}

export async function submitCode(params) {
  return service("submit_code", params, "post");
}

export async function aiChat(params) {
  return service("ai_chat", params, "post");
}

export async function aiFeedbackStatus(params) {
  return service("ai_feedback_status", params);
}

export async function runCode(params) {
  return service("run_code", params, "post");
}

export async function rerunSubmissionAutograder(params) {
  return service("rerun_submission_autograder", params, "post");
}

export async function exportSubmissions(params) {
  return service("export_submissions", params, "get", {
    responseType: "blob",
    skipGlobalErrorMessage: true,
  });
}

export async function publishGrades(params) {
  return service("publish_grades", params, "post");
}

