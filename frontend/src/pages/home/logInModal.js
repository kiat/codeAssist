import { Button, Form, Input, message, Modal } from "antd";
import { useContext } from "react";
import { GlobalContext } from "../../App";
import axios from "axios";

/**
 * login modal
 * @param {*} param0
 * @returns
 */
export default function LogInModal({ open, onCancel, logIn }) {
  const { updateUserInfo } = useContext(GlobalContext);

  // login action
  const onSubmit = values => {
    axios
      .post("/logIn", values)
      .then(res => {
        if (res.data.status === 1) {
          const { name, isStudent } = res.data.data;
          const userInfo = { name, isStudent };
          localStorage.setItem("userInfo", JSON.stringify(userInfo));
          updateUserInfo(userInfo);
        } else {
          message.error("Login failed");
        }
      })
      .catch(err => {
        message.error("Connecting failed");
      });
    return;
  };
  return (
    <Modal open={open} footer={null} onCancel={onCancel}>
      <Form layout='vertical' onFinish={onSubmit}>
        <Form.Item label='Email' name='email'>
          <Input />
        </Form.Item>
        <Form.Item label='Password' name='password'>
          <Input />
        </Form.Item>
        <Form.Item>
          <Button type='primary' htmlType='submit'>
            Log In
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
}
