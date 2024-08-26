import { Button, Form, Input, Modal, Radio } from "antd";
import { useState, useContext, useEffect } from "react";
import { GlobalContext } from "../../App";
// import axios from "axios";
import { userLogin } from "../../services/user";

/**
 * login window modal
 * @param {*} param0
 * @returns
 */
export default function LogInModal({ open, onCancel, logIn }) {
  const { updateUserInfo } = useContext(GlobalContext);
  const [displayLogin, setDisplayLogin] = useState(true);

  // login action
  const onSubmit = async (values) => {
    // const isStudent = values.isStudent;
    const {...restValue } = values;
    let res;
    // let ta_res;
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
      if (error.response) {
        alert('User authentication failed. Invalid Username/Password combination');
      }
    }
  };

  const handleCancel = () => {
    setDisplayLogin(true);
    onCancel();
  };

  const displayLoginPage = () => {
    setDisplayLogin(true);
  }

  const changePassword = async (values) => {
    const { email, ...restValues } = values;
    console.log(email, restValues);
  };


    // Create state for whether or not forgot password is pressed - if pressed, then change modal display
    // Find what primary id key is - send email with link to reset password
    // If valid email, then send a link to reset the password

  return (
<<<<<<< HEAD
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
=======
    <Modal title="LOG IN" open={open} footer={null} onCancel={handleCancel}>
      {displayLogin ? (
        <>
          <Form layout="vertical" onFinish={onSubmit}>
            <Form.Item name="isStudent" initialValue={1}>
              <Radio.Group
                optionType="button"
                buttonStyle="solid"
                style={{ width: "100%" }}
              >
                <Radio.Button
                  value={0}
                  style={{ width: "50%", textAlign: "center" }}
                >
                  Instructor
                </Radio.Button>
                <Radio.Button
                  value={1}
                  style={{ width: "50%", textAlign: "center" }}
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

          <Button
            style={{ border: 0, backgroundColor: "transparent", padding: 0, textAlign: "left"}}
            onClick={() => setDisplayLogin(false)}
          >
            Forgot Password?
>>>>>>> a20e6b7 (Adding initial frontend page for change password)
          </Button>
        </>
      ) : (
        <>
          <Form layout="vertical" onFinish={changePassword}> 
            <Form.Item label="Email" name="email">
              <Input placeholder="Enter your email" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit">
                Send Verification
              </Button>
            </Form.Item>
          </Form>
        </>
      )}   
    </Modal>
  );
}
