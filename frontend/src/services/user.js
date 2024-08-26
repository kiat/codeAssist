import service from ".";

export async function signUpUser(params) {
<<<<<<< HEAD
  return service("create_user", params, "post");
=======
  return service("create_new_user", params, "post");
}

export async function signUpStudent(params) {
  return service("create_student", params, "post");
  // return {
  //   data: {
  //     id: 123456,
  //     name: "aaa bbb",
  //   },
  // };
>>>>>>> c8f5145 (Working functionality with google login)
}

export async function get_user(params) {
  return service("get_users", params, "get");
}

export async function userLogin(params) {
  return service("user_login", params, "post");
}

<<<<<<< HEAD
export async function googleLogin(params) {
=======
export async function studentLogin(params) {
  return service("student_login", params, "post");
}

export async function instructorLogin(params) {
  return service("instructor_login", params, "post");
}

export async function userLogin(params) {
>>>>>>> c8f5145 (Working functionality with google login)
  return service("google_login", params, "post");
}