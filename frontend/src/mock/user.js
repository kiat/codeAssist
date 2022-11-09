import IMock from "./common";
import { FAIL, SUCCESS } from "./constant";

// 测试登录接口均返回学生身份
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

// 注册接口
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
