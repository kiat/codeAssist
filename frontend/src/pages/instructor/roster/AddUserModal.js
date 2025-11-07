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

export default ({ open, toggleAddModalOpen }) => {
  return (
    <Modal
      open={open}
      title='Add a User'
      footer={null}
      onCancel={toggleAddModalOpen}
    >
      <Form layout='vertical'>
        <Form.Item>
          <Row gutter={20}>
            <Col span={12}>
              <Form.Item label='FIRST NAME' NAME='firstName'>
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              {" "}
              <Form.Item label='LAST NAME' NAME='lastName'>
                <Input />
              </Form.Item>
            </Col>
          </Row>
        </Form.Item>
        <Form.Item label='EMAIL ADDRESS' name='emailAddress'>
          <Input />
        </Form.Item>
        <Form.Item label='STUDENT ID # (OPTIONAL)' name='emailAddress'>
          <Input />
        </Form.Item>
        <Form.Item label='SECTIONS' name='sections'>
          <Select
            options={[
              { label: "c-test123456", value: "1" },
              { label: "c-test123457", value: "2" },
              { label: "c-test123458", value: "3" },
            ]}
          />
        </Form.Item>
        <Form.Item label='ROLE' name='role'>
          <Radio.Group options={["Student", "Instructor", "TA", "Reader"]} />
        </Form.Item>
        <Form.Item label='EMAIL NOTIFICATION' name='emailNotification'>
          <Checkbox>
            Let this user know that they were added to the course
          </Checkbox>
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type='primary'>Submit</Button>
            <Button type='primary' danger onClick={toggleAddModalOpen}>
              Cancel
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};
