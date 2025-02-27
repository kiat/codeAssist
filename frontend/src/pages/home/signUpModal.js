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
  // const [isStudent, setIsStudent] = useState(false);

  // action after successfully signup
  const finishSignUp = async (values) => {
    const {role, ...restValue } = values;
    // const isStudent = values.isStudent;
    let res;
    // let taRes;
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
        <Form.Item name="role" initialValue='student'>
          <Radio.Group
            optionType="button"
            buttonStyle="solid"
            style={{ width: "100%" }}
          >
            <Radio.Button
              value='instructor'
              style={{ width: "33%", textAlign: "center" }}
            >
              Instructor
            </Radio.Button>
            <Radio.Button
              value='student'
              style={{ width: "33%", textAlign: "center" }}
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
        <Form.Item label="Email" name="email_address">
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
