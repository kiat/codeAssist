import IMock from "./common";
import { FAIL, SUCCESS } from "./constant";

// 
//test: login port return student identity
IMock(
  "/logIn",
  function (params) {
    if (/\w+@\w+\.com/.test(params.email)) {
      return {
        ...SUCCESS,
        data: {
          name: "student123",
          isStudent: 1,
        },
      };
    } else {
      return FAIL;
    }
  },
  "post"
);

// sign up port
IMock(
  "/signUp",
  function (params) {
    const { userName, isStudent, email } = params;
    if (/\w+@\w+\.com/.test(email)) {
      return {
        ...SUCCESS,
        data: {
          name: userName,
          isStudent: isStudent,
        },
      };
    } else {
      return FAIL;
    }
  },
  "post"
);
