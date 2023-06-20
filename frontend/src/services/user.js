import service from ".";

export async function signUpStudent(params) {
  return service("create_student", params, "post");
  // return {
  //   data: {
  //     id: 123456,
  //     name: "aaa bbb",
  //   },
  // };
}

/**
 * signUpInstructor POSTs a new instructor to the database
 * @param {*} params the data for the new instructor
 * @returns 
 */
export async function signUpInstructor(params) {
  return service("create_instructor", params, "post");
  // return {
  //   data: {
  //     id: 123456,
  //     name: "aaa bbb",
  //   },
  // };
}

export async function studentLogin(params) {
  return service("student_login", params, "post");
}

export async function instructorLogin(params) {
  return service("instructor_login", params, "post");
}
