import {
  Button,
  Checkbox,
  Col,
  Form,
  Input,
  Modal,
  Radio,
  Row,
  Select,
  Space,
} from "antd";

export default ({ open, toggleAddModalOpen, onFinish }) => {
  return (
    <Modal
      open={open}
      title="Add a User"
      footer={null}
      onCancel={toggleAddModalOpen}
    >
      <Form layout="vertical" onFinish={onFinish}>
        <Form.Item label="EMAIL" name="email">
          <Input />
        </Form.Item>
        <Form.Item label="ROLE" name="role">
          <Radio.Group options={["Student", "Instructor", "TA"]} />
        </Form.Item>
        <Form.Item
          label="EMAIL NOTIFICATION"
          name="emailNotification"
          valuePropName="checked"
        >
          <Checkbox>
            Let this user know that they were added to the course
          </Checkbox>
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">
              Submit
            </Button>
            <Button type="primary" danger onClick={toggleAddModalOpen}>
              Cancel
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};
