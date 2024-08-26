import { Button, Form, Input, Modal, Radio } from "antd";
import { useContext, useEffect, useState } from "react";
import { GlobalContext } from "../../App";
// import axios from "axios";
import { instructorLogin, studentLogin } from "../../services/user";

/**
 * login window modal
 * @param {*} param0
 * @returns
 */
export default function LogInModal({ open, onCancel, logIn }) {
  const { updateUserInfo } = useContext(GlobalContext);

  // login action
  const onSubmit = async (values) => {
    // const isStudent = values.isStudent;
    const { isStudent, ...restValue } = values;
    let res;
    try {
      res = await userLogin(restValue);
      if (res) {
        const userInfo = {
          name: res.data?.name,
          id: res.data?.id,
          isStudent,
        };
        localStorage.setItem("userInfo", JSON.stringify(userInfo));
        updateUserInfo(userInfo);
      } 
    }
    
    catch (error) {
      if (error.response) {
        alert('User authentication failed. Invalid Username/Password combination');
      }
    }
    // axios
    //   .post("/logIn", values)
    //   .then(res => {
    //     if (res.data.status === 1) {
    //       const { name, isStudent } = res.data.data;
    //       const userInfo = { name, isStudent };
    //       localStorage.setItem("userInfo", JSON.stringify(userInfo));
    //       updateUserInfo(userInfo);
    //     } else {
    //       message.error("login failed");
    //     }
    //   })
    //   .catch(err => {
    //     message.error("connection failed");
    //   });
    // return;
  };

  const handleCancel = () => {
    onCancel();
  };

  return (
    <Modal title="LOG IN" open={open} footer={null} onCancel={handleCancel}>
      <Form layout="vertical" onFinish={onSubmit}>
        <Form.Item name="isStudent" initialValue={1} style={{ width: "100%" }}>
          <Radio.Group
            optionType="button"
            buttonStyle="solid"
            style={{ display: "flex", width: "100%" }}
          >
            <Radio.Button
              value={0}
              style={{ flex: 1, textAlign: "center" }}
            >
              Instructor
            </Radio.Button>
            <Radio.Button
              value={1}
              style={{ flex: 1, textAlign: "center" }}
            >
              Student
            </Radio.Button>
          </Radio.Group>
        </Form.Item>
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