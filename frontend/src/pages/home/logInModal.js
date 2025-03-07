import { Button, Form, Input, Modal } from "antd";
import { useContext } from "react";
import { GlobalContext } from "../../App";
import { userLogin } from "../../services/user";

/**
 * login window modal
 * @param {*} param0
 * @returns
 */
export default function LogInModal({ open, onCancel }) {
  const { updateUserInfo } = useContext(GlobalContext);

  // login action
  const onSubmit = async (values) => {
    const {...restValue } = values;
    let res;
    try {

      res = await userLogin(restValue);

      if (res) {
        const userInfo = {
          name: res.data?.name,
          id: res.data?.id,
          isStudent: res.data?.role === 'student',
          role: res.data?.role
        };
        localStorage.setItem("userInfo", JSON.stringify(userInfo));
        updateUserInfo(userInfo);
      } 
    } catch (error) {
      console.log("error", error);
    }
  };
  return (
    <Modal title="LOG IN" open={open} footer={null} onCancel={onCancel}>
      <Form layout="vertical" onFinish={onSubmit}>
        <Form.Item label="Email" name="email">
          <Input placeholder="Your Email" />
        </Form.Item>
        <Form.Item label="Password" name="password">
          <Input.Password placeholder="Your Password" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">
            Log In
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
}
