import {
  Checkbox,
  Col,
  Form,
  Modal,
  Row,
  Select,
  Space,
  Typography,
} from "antd";

export default ({ open, onCancel }) => {
  return (
    <Modal open={open} onCancel={onCancel} title='Add an Extension'>
      <Form layout='vertical'>
        <Form.Item label='STUDENT'>
          <Select
            showSearch
            placeholder='Search students by name or email'
            filterOption={(input, option) =>
              option.label.toLowerCase().includes(input.toLowerCase())
            }
            options={[
              { label: "aaa - aaa@example.com", value: "aaa" },
              { label: "aaa2 - aaa2@example.com", value: "aaa2" },
              { label: "aaa3 - aaa3@example.com", value: "aaa3" },
              { label: "aaa4 - aaa4@example.com", value: "aaa4" },
              { label: "aaa5 - aaa5@example.com", value: "aaa5" },
            ]}
          />
        </Form.Item>
        <div
          style={{
            backgroundColor: "#f8f9f9",
            paddingTop: "15px",
            paddingLeft: "15px",
            marginBottom: "20px",
          }}
        >
          <Row>
            <Col span={12}>
              <div>
                <Typography.Title level={5}>
                  RELEASE DATE (CST)
                </Typography.Title>
                <Typography.Paragraph>May 1,2022 6:00 AM</Typography.Paragraph>
              </div>
              <div>
                <Typography.Title level={5}>
                  LATE DUE DATE (CST)
                </Typography.Title>
                <Typography.Paragraph>May 1,2022 6:00 AM</Typography.Paragraph>
              </div>
            </Col>
            <Col span={12}>
              <div>
                <Typography.Title level={5}>DUE DATE (CST)</Typography.Title>
                <Typography.Paragraph>May 1,2022 6:00 AM</Typography.Paragraph>
              </div>
              <div>
                <Typography.Title level={5}>TIME LIMIT</Typography.Title>
                <Typography.Paragraph>--</Typography.Paragraph>
              </div>
            </Col>
          </Row>
        </div>
        <Form.Item label='EXTENSION TYPE'>
          <Checkbox.Group>
            <Space direction='vertical'>
              <Checkbox>Release Date</Checkbox>
              <Checkbox>Due Date</Checkbox>
              <Checkbox>Late Due Date</Checkbox>
            </Space>
          </Checkbox.Group>
        </Form.Item>
      </Form>
    </Modal>
  );
};
