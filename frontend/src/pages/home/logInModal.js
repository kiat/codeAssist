import { Button, Form, Input, Modal, Radio } from "antd";
import { useState, useContext } from "react";
import { GlobalContext } from "../../App";
// import axios from "axios";
import { instructorLogin, studentLogin, taLogin, userLogin } from "../../services/user";

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
    const {...restValue } = values;
    // const {isTA, ...secondRestValue} = values;
    let res;
    // let ta_res;
    try {

      res = await userLogin(restValue);
      
      // if (role == 'student'){
      //   setIsStudent(true);
      // }

      // if (ta_res){
      //   const userInfo = {
      //     name: secondRestValue.data?.name,
      //     id: secondRestValue.data?.id,
      //     isStudent: isStudent,
      //   };
      //   localStorage.setItem("userInfo", JSON.stringify(userInfo));
      //   updateUserInfo(userInfo);
      // }

      if (res) {
        const userInfo = {
          name: res.data?.name,
          id: res.data?.id,
          isStudent: res.data?.role === 'student',
          isTA: res.data?.role == 'TA',
        };
        localStorage.setItem("userInfo", JSON.stringify(userInfo));
        updateUserInfo(userInfo);
      } 
    } catch (error) {
      if (error.response) {
        alert('User authentication failed. Invalid Username/Password combination');
      }
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
