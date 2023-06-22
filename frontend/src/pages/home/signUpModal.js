import { Button, Form, Input, Modal, Radio } from "antd";
// import axios from "axios";
import { useContext } from "react";
import { GlobalContext } from "../../App";
// import service from "../../services";
import { signUpInstructor, signUpStudent } from "../../services/user";

/**
 * user signup window modal
 * @param {*} param0
 * @returns
 */
export default function SignUpModal({ open, onCancel }) {
  const { updateUserInfo } = useContext(GlobalContext);

  // action after successfully signup
  const finishSignUp = async (values) => {
    const { isStudent, ...restValue } = values;
    // const isStudent = values.isStudent;
    let res;
    if (isStudent) {
      res = await signUpStudent(restValue);
    } else {
      res = await signUpInstructor(restValue);
    }
    if (res) {
      const userInfo = {
        name: res.data?.name,
        id: res.data?.id,
        isStudent,
      };
      localStorage.setItem("userInfo", JSON.stringify(userInfo));
      updateUserInfo(userInfo);
    }

    // axios
    //   .post("/signUp", values)
    //   // .post("http://127.0.0.1:4523/m1/1927806-0-default/create_student", values)
    //   .then(res => {
    //     if (res.data.status === 1) {
    //       const { name, isStudent } = res.data.data;
    //       const userInfo = { name, isStudent };
    //       localStorage.setItem("userInfo", JSON.stringify(userInfo));
    //       updateUserInfo(userInfo);
    //     } else {
    //       message.error("signup failed");
    //     }
    //   })
    //   .catch(err => {
    //     message.error("connection failed");
    //   });
    // return;
  };

  return (
    <Modal title="SIGN UP" open={open} footer={null} onCancel={onCancel}>
      <Form layout="vertical" onFinish={finishSignUp}>
        <Form.Item name="isStudent" initialValue={1}>
          <Radio.Group
            optionType="button"
            buttonStyle="solid"
            style={{ width: "100%" }}
          >
            <Radio.Button
              value={0}
              style={{ width: "50%", textAlign: "center" }}
            >
              Instructor
            </Radio.Button>
            <Radio.Button
              value={1}
              style={{ width: "50%", textAlign: "center" }}
            >
              Student
            </Radio.Button>
          </Radio.Group>
        </Form.Item>
        <Form.Item label="EID" name="eid">
          <Input placeholder="Your EID" />
        </Form.Item>
        <Form.Item label="Name" name="name">
          <Input placeholder="Your Name" />
        </Form.Item>
        <Form.Item label="Email" name="email">
          <Input placeholder="email@example.com" />
        </Form.Item>
        <Form.Item label="Password" name="password">
          <Input.Password placeholder="Your Password" />
        </Form.Item>
        <Form.Item>
          <Button style={{ width: "100%" }} type="primary" htmlType="submit">
            Sign Up
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
}
