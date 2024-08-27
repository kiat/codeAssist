import React, { useContext } from 'react'
import { Button, Form, Input, Modal, Radio } from "antd";
// import axios from "axios";
import { GlobalContext } from "../../App";
// import service from "../../services";
import { signUpInstructor, signUpStudent, signUpUser } from "../../services/user";

function GoogleSignUp({ open, onCancel, googleValues }) {
  const { updateUserInfo } = useContext(GlobalContext);

  const finishSignUp = async (values) => {
    values["credential"] = googleValues.credential;
    // console.log(values)

    let res;
    try {
      res = await create_google_user(values);

      if (res) {
        const userInfo = {
          name: res.data?.name,
          email: googleValues.email,
          id: res.data?.id,
          isStudent: res.data?.student,
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
          <Form.Item name="role" initialValue={1} style={{ width: "100%" }}>
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