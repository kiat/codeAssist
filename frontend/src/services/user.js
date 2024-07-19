import service from ".";

export async function signUpUser(params) {
  return service("create_user", params, "post");
}

export async function getUser(params) {
  return service("get_user", params, "get");
}

export async function userLogin(params) {
  return service("user_login", params, "post");
}