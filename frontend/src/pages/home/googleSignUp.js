import React, { useContext } from 'react'
import { Button, Form, Input, Modal, Typography } from "antd";
// import axios from "axios";
import { GlobalContext } from "../../App";
// import service from "../../services";
import { googleSignUp } from "../../services/user";

function GoogleSignUp({ open, onCancel, googleValues }) {
  const { updateUserInfo } = useContext(GlobalContext);

  const finishSignUp = async (values) => {
    values["credential"] = googleValues.credential;
    // Instructor accounts are created by an admin, not through sign-up.
    values["role"] = "student";

    let res;
    try {
      res = await googleSignUp(values);

      if (res) {
        const userInfo = {
          name: res.data?.name,
          email: googleValues.email,
          id: res.data?.id,
          isStudent: res.data?.role === "student",
          isAdmin: res.data?.role === "admin",
          role: res.data?.role,
        };

        localStorage.setItem("userInfo", JSON.stringify(userInfo));
        updateUserInfo(userInfo);
      }
    }
    catch (error) {
      if (error.response) {
        alert('User creation failed. Please try again');
      }
    }

  };

  return (
    <div>
      <Modal title="Finish Sign Up" open={open} footer={null} onCancel={onCancel}>
        <Form layout="vertical" onFinish={finishSignUp}>
          <Typography.Paragraph type="secondary">
            Sign up as a student. Instructors: ask an administrator to create your account.
          </Typography.Paragraph>
          <Form.Item label="EID" name="eid">
            <Input placeholder="Your EID" />
          </Form.Item>
          <Form.Item label="Name" name="name">
            <Input placeholder="Your Name" />
          </Form.Item>
          <Form.Item>
            <Button style={{ width: "100%" }} type="primary" htmlType="submit">
              Sign Up
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default GoogleSignUp
