import { Button, Form, Input, Modal, message } from "antd";
import { useContext, useState } from "react";
import { GlobalContext } from "../../App";
import { userLogin, resetPasswordRequest } from "../../services/user";

/**
 * login window modal
 * @param {*} param0
 * @returns
 */
export default function LogInModal({ open, onCancel }) {
  const { updateUserInfo } = useContext(GlobalContext);
  const [resetModalOpen, setResetModalOpen] = useState(false);

  // login action
  const onSubmit = async (values) => {
    try {
      const res = await userLogin(values);
      if (res) {
        const userInfo = {
          name: res.data?.name,
          id: res.data?.id,
          isStudent: res.data?.role === "student",
          role: res.data?.role,
        };
        localStorage.setItem("userInfo", JSON.stringify(userInfo));
        updateUserInfo(userInfo);
      }
    } catch (error) {
      console.log("Login error:", error);
      message.error("Invalid email or password.");
    }
  };

  return (
    <>
      <Modal title="LOG IN" open={open} footer={null} onCancel={onCancel}>
        <Form layout="vertical" onFinish={onSubmit}>
          <Form.Item label="Email" name="email" rules={[{ required: true, message: "Please enter your email!" }]}>
            <Input placeholder="Your Email" />
          </Form.Item>
          <Form.Item label="Password" name="password" rules={[{ required: true, message: "Please enter your password!" }]}>
            <Input.Password placeholder="Your Password" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">
              Log In
            </Button>
          </Form.Item>
        </Form>
        <p style={{ textAlign: "center" }}>
          <Button type="link" onClick={() => setResetModalOpen(true)}>
            Forgot Password?
          </Button>
        </p>
      </Modal>

      {/* Forgot Password Modal */}
      <ForgotPasswordModal open={resetModalOpen} onCancel={() => setResetModalOpen(false)} />
    </>
  );
}

/**
 * Forgot Password Modal
 */
function ForgotPasswordModal({ open, onCancel }) {
  const [loading, setLoading] = useState(false);

  const onSubmit = async (values) => {
    setLoading(true);
    try {
      await resetPasswordRequest(values.email);
      message.success("A password reset email has been sent!");
      onCancel(); // Close modal after success
    } catch (error) {
      console.log("Reset password error:", error);
      message.error("Failed to send reset email. Please try again.");
    }
    setLoading(false);
  };

  return (
    <Modal title="Forgot Password?" open={open} footer={null} onCancel={onCancel}>
      <Form layout="vertical" onFinish={onSubmit}>
        <Form.Item label="Email" name="email" rules={[{ required: true, type: "email", message: "Please enter a valid email!" }]}>
          <Input placeholder="Enter your email" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            Reset Password
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
}
