import { Button, Form, Input, Result } from "antd";
import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { resetPassword } from "../../services/user";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const token = searchParams.get("token");

  const onSubmit = async (values) => {
    if (!token) return;
    setLoading(true);
    try {
      await resetPassword({ token, password: values.password });
      setSuccess(true);
    } catch {
      // Error shown by axios interceptor
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <Result
        status="error"
        title="Invalid Reset Link"
        subTitle="This password reset link is invalid or missing a token."
        extra={
          <Button type="primary" onClick={() => navigate("/")}>
            Back to Home
          </Button>
        }
      />
    );
  }

  if (success) {
    return (
      <Result
        status="success"
        title="Password Reset Successfully"
        subTitle="You can now log in with your new password."
        extra={
          <Button type="primary" onClick={() => navigate("/")}>
            Go to Login
          </Button>
        }
      />
    );
  }

  return (
    <div style={{ maxWidth: 400, margin: "80px auto", padding: "0 24px" }}>
      <h2>Reset Your Password</h2>
      <Form layout="vertical" onFinish={onSubmit}>
        <Form.Item
          label="New Password"
          name="password"
          rules={[
            { required: true, message: "Please enter a new password" },
            { min: 6, message: "Password must be at least 6 characters" },
          ]}
        >
          <Input.Password placeholder="New password" />
        </Form.Item>
        <Form.Item
          label="Confirm Password"
          name="confirmPassword"
          dependencies={["password"]}
          rules={[
            { required: true, message: "Please confirm your password" },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue("password") === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error("Passwords do not match"));
              },
            }),
          ]}
        >
          <Input.Password placeholder="Confirm new password" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            Reset Password
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
}
