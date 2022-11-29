import { DeleteOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Checkbox,
  Col,
  DatePicker,
  Form,
  Input,
  PageHeader,
  Row,
  Select,
  Space,
} from "antd";

export default () => {
  return (
    <>
      <PageHeader title='Edit Programming Assignment' />
      <Form layout='vertical'>
        <Card bordered={false} title='Basic Settings'>
          {/* <Form.Item label='TITLE'> */}
          <Form.Item label={<span>TITLE</span>}>
            <Input />
          </Form.Item>
          <Form.Item label='SUBMISSION ANONYMIZATION'>
            <Checkbox>Enable Anonymous Grading</Checkbox>
            <div style={{ marginLeft: "24px", color: "grey" }}>
              Hide identifiable student information from being listed with
              submissions.
            </div>
          </Form.Item>
          <Form.Item label='CANVAS ASSIGNMENT'>
            <Space>
              <Input style={{ width: "205px" }} />
              <Button>Change</Button>
              <Button danger type='primary'>
                Unlink
              </Button>
            </Space>
          </Form.Item>
          <Form.Item>
            <Row gutter={20}>
              <Col>
                <Form.Item label='RELEASE DATE (CST)'>
                  <DatePicker showTime />
                </Form.Item>
                <Form.Item>
                  <Checkbox>Allow Late Submissions</Checkbox>
                </Form.Item>
              </Col>
              <Col>
                <Form.Item label='DUE DATE (CST)'>
                  <DatePicker showTime />
                </Form.Item>
                <Form.Item label='LATE DUE DATE (CST)'>
                  <DatePicker showTime />
                </Form.Item>
              </Col>
            </Row>
          </Form.Item>
          <Form.Item label='GROUP SUBMISSION'>
            <Checkbox>Enable Group Submission</Checkbox>
          </Form.Item>
          <Form.Item label='LIMIT GROUP SIZE'>
            <Input placeholder='No Max' />
          </Form.Item>
          <Form.Item label='MANUAL GRADING'>
            <Checkbox>Enable Manual Grading</Checkbox>
          </Form.Item>
          <Form.Item label='LEADERBOARD'>
            <Checkbox>Enable Leaderboard</Checkbox>
          </Form.Item>
          <Form.Item label='DEFAULT NUMBER OF ENTRIES SHOWN'>
            <Input placeholder='No Max' />
          </Form.Item>
          <Form.Item label='SUBMISSION METHODS ENABLED'>
            <Space direction='vertical'>
              <Checkbox>Upload</Checkbox>
              <Checkbox>GitHub</Checkbox>
              <Checkbox>Bitbucket</Checkbox>
            </Space>
          </Form.Item>
          <Form.Item label='IGNORED FILES'>
            <Input.TextArea />
            <span style={{ color: "grey" }}>Follows gitignore format.</span>
          </Form.Item>
        </Card>
        <Card bordered={false} title='Autograder Settings'>
          <Form.Item
            label={
              <Space direction='vertical'>
                <div>CONTAINER SPECIFICATIONS</div>
                <div style={{ color: "grey" }}>
                  Your autograder will have access to at least the portion of
                  CPU allocated, and at most the memory allocated.
                </div>
              </Space>
            }
          >
            <Space direction='vertical'>
              <Checkbox>0.5 CPU, 0.75GB RAM</Checkbox>
              <Checkbox>1.0 CPU, 1.5GB RAM</Checkbox>
              <Checkbox>2.0 CPU, 3.0GB RAM</Checkbox>
              <Checkbox>4.0 CPU, 6.0GB RAM</Checkbox>
            </Space>
          </Form.Item>
          <Form.Item
            label={
              <Space direction='vertical'>
                <div>AUTOGRADER TIMEOUT</div>
                <div style={{ color: "grey" }}>
                  Your autograder will be timed out after this amount of time.
                </div>
              </Space>
            }
          >
            <Select
              options={[
                { label: "10 minutes", value: "10" },
                { label: "20 minutes", value: "20" },
              ]}
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type='primary'>Save</Button>
              <Button danger type='primary' icon={<DeleteOutlined />}>
                Delete assignment
              </Button>
            </Space>
          </Form.Item>
        </Card>
      </Form>
    </>
  );
};
