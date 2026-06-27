import { Button, Form, Input, Modal, message } from "antd";
import { useState } from "react";
import { forgotPassword } from "../../services/user";

export default function ForgotPasswordModal({ open, onCancel }) {
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const onSubmit = async (values) => {
    setLoading(true);
    try {
      await forgotPassword({ email: values.email });
      setSubmitted(true);
    } catch {
      // Error is shown by the axios interceptor
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setSubmitted(false);
    onCancel();
  };

  return (
    <Modal title="FORGOT PASSWORD" open={open} footer={null} onCancel={handleCancel}>
      {submitted ? (
        <p>
          If an account with that email exists, a password reset link has been
          sent. Please check your inbox.
        </p>
      ) : (
        <Form layout="vertical" onFinish={onSubmit}>
          <p style={{ marginBottom: 16 }}>
            Enter your email address and we'll send you a link to reset your
            password.
          </p>
          <Form.Item
            label="Email"
            name="email"
            rules={[
              { required: true, message: "Please enter your email" },
              { type: "email", message: "Please enter a valid email address" },
            ]}
          >
            <Input placeholder="email@example.com" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              Send Reset Link
            </Button>
          </Form.Item>
        </Form>
      )}
    </Modal>
  );
}
