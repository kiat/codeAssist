import { Button, Form, Input, Modal, Radio } from "antd";
// import axios from "axios";
import { useState, useContext } from "react";
import { GlobalContext } from "../../App";
// import service from "../../services";
import { signUpUser } from "../../services/user";

/**
 * user signup window modal
 * @param {*} param0
 * @returns
 */
export default function SignUpModal({ open, onCancel }) {
  const { updateUserInfo } = useContext(GlobalContext);

  // action after successfully signup
  const finishSignUp = async (values) => {
    const {role, ...restValue } = values;
    // const isStudent = values.isStudent;
    let res;
    res = await signUpUser({...restValue, role});

    if (res) {
      const userInfo = {
        name: res.data?.name,
        id: res.data?.id,
        isStudent: role === 'student',
        role: role
      };
      localStorage.setItem("userInfo", JSON.stringify(userInfo));
      updateUserInfo(userInfo);
    }

  };  

  return (
    <Modal title="SIGN UP" open={open} footer={null} onCancel={onCancel}>
      <Form layout="vertical" onFinish={finishSignUp}>
<<<<<<< HEAD
        <Form.Item name="role" initialValue='student'>
=======
        <Form.Item name="isStudent" initialValue={1} style={{ width: "100%" }}>
>>>>>>> c8f5145 (Working functionality with google login)
          <Radio.Group
            optionType="button"
            buttonStyle="solid"
            style={{ display: "flex", width: "100%" }}
          >
            <Radio.Button
<<<<<<< HEAD
              value='instructor'
              style={{ width: "33%", textAlign: "center" }}
=======
              value={0}
              style={{ flex: 1, textAlign: "center" }}
>>>>>>> c8f5145 (Working functionality with google login)
            >
              Instructor
            </Radio.Button>
            <Radio.Button
<<<<<<< HEAD
              value='student'
              style={{ width: "33%", textAlign: "center" }}
=======
              value={1}
              style={{ flex: 1, textAlign: "center" }}
>>>>>>> c8f5145 (Working functionality with google login)
            >
              Student
            </Radio.Button>
            <Radio.Button
              value='Reader'
              style={{ width: "33%", textAlign: "center" }}
            >
              Reader
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
