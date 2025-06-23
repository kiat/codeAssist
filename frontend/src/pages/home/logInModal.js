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
    const { ...restValue } = values;
    let res;
    try {
      res = await userLogin(restValue);

      if (res) {
        const userInfo = {
          name: res.data?.name,
          id: res.data?.id,
          isStudent: res.data?.role === "student",
          isAdmin: res.data?.role === "admin",
          role: res.data?.role,
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
      <Button
        style={{ width: "100%", marginBottom: 16, display: "flex", alignItems: "center", justifyContent: "center" }}
        type="default"
        onClick={() => window.location.href = "http://localhost:5000/login/google"}
      >
        <img
          src="https://developers.google.com/identity/images/g-logo.png"
          alt="Google"
          style={{ width: 20, height: 20, marginRight: 8 }}
        />
        Login with Google
      </Button>
      <Form layout="vertical" onFinish={onSubmit}>
        <Form.Item
          label="Email"
          name="email"
          rules={[
            {
              required: true,
              message: "Please enter your email",
            },
            {
              type: "email",
              message: "Please enter a valid email address",
            },
          ]}
        >
          <Input placeholder="email@example.com" />
        </Form.Item>

        <Form.Item
          label="Password"
          name="password"
          rules={[
            {
              required: true,
              message: "Please enter your password",
            },
            {
              min: 6,
              message: "Password must be at least 6 characters",
            },
          ]}
        >
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
