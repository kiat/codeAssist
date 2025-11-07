import service from ".";

export async function createUser(params) {
  return service("create_user", params, "post");
}

export async function get_user(params) {
  return service("get_user", params, "get");
}

export async function getUserByEmail(params) {
  return service("get_user_by_email", params);
}

export async function userLogin(params) {
  return service("user_login", params, "post");
}

export async function googleSignUp(params) {
  return service("create_google_user", params, "post");
}

export async function googleLogin(params) {
  return service("google_login", params, "post");
}


