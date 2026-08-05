import {
  Button,
  Checkbox,
  Form,
  Input,
  Modal,
  Radio,
  Space,
} from "antd";

export default ({ open, toggleAddModalOpen, onFinish }) => {
  const [form] = Form.useForm();

  const handleCancel = () => {
    form.resetFields();
    toggleAddModalOpen();
  };

  const handleFinish = async (values) => {
    await onFinish(values);
    form.resetFields();
  };

  return (
    <Modal
      open={open}
      title="Add a User"
      footer={null}
      onCancel={handleCancel}
    >
      <Form layout="vertical" onFinish={handleFinish} form={form}>
        <Form.Item label="EMAIL" name="email">
          <Input />
        </Form.Item>
        <Form.Item label="ROLE" name="role">
          <Radio.Group options={["student", "instructor", "TA"]} />
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
            <Button type="primary" danger onClick={handleCancel}>
              Cancel
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};
