import { Button, Form, Input, Modal, Radio } from "antd";
import { useContext } from "react";
import { GlobalContext } from "../../App";
import { createUser } from "../../services/user";

/**
 * user signup window modal
 * @param {*} param0
 * @returns
 */
export default function SignUpModal({ open, onCancel }) {
  const { updateUserInfo } = useContext(GlobalContext);

  // action after successfully signup
  const finishSignUp = async (values) => {
    const { role, ...restValue } = values;

    try {
      const res = await createUser({ ...restValue, role });

      if (res) {
        const userInfo = {
          name: res.data?.name,
          id: res.data?.id,
          isStudent: role === "student",
          isAdmin: role === "admin",
          role: role,
        };
        localStorage.setItem("userInfo", JSON.stringify(userInfo));
        updateUserInfo(userInfo);
      }
    } catch (error) {
      console.log("Error creating user: ", error);
    }
  };

  return (
    <Modal title="SIGN UP" open={open} footer={null} onCancel={onCancel}>
      <Form layout="vertical" onFinish={finishSignUp}>
        <Form.Item name="role" initialValue="student">
          <Radio.Group optionType="button" buttonStyle="solid" style={{ width: "100%" }}>
            <Radio.Button value="student" style={{ width: "50%", textAlign: "center" }}>
              Student
            </Radio.Button>
            <Radio.Button value="instructor" style={{ width: "50%", textAlign: "center" }}>
              Instructor
            </Radio.Button>
          </Radio.Group>
        </Form.Item>
        <Form.Item label="EID" name="eid" rules={[{ required: true, message: "Please enter your eid" }]}>
          <Input placeholder="Your EID" />
        </Form.Item>
        <Form.Item label="Name" name="name" rules={[{ required: true, message: "Please enter your name" }]}>
          <Input placeholder="John Doe" />
        </Form.Item>
        <Form.Item
          label="Email"
          name="email_address"
          rules={[
            { required: true, message: "Please enter your email" },
            { type: "email", message: "Please enter a valid email address" },
          ]}
        >
          <Input placeholder="email@example.com" />
        </Form.Item>
        <Form.Item
          label="Password"
          name="password"
          rules={[
            { required: true, message: "Please enter a password" },
            { min: 6, message: "Password must be at least 6 characters" },
          ]}
        >
          <Input.Password placeholder="Your Password" />
        </Form.Item>
        <Form.Item>
          <Button style={{ width: "100%" }} type="primary" htmlType="submit">
            Sign Up
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
}
