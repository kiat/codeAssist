import { Alert, Button, Form, Input } from "antd";

export default function RelationForm({ onFinish, onCancel }) {
  return (
    <>
      <div
        style={{
          marginBottom: "10px",
        }}
      >
        <Alert
          message='Use your instructor-provided entry code to enroll in the course'
          type='info'
          banner
        />
      </div>
      <Form layout='vertical' onFinish={onFinish}>
        <Form.Item label='COURSE ENTRY CODE' name='entryCode'>
          <Input placeholder='enter your course entry code' />
        </Form.Item>
        <Form.Item>
          <Button
            type='primary'
            style={{ marginRight: "10px" }}
            htmlType='submit'
          >
            Add course
          </Button>
          <Button type='danger' onClick={onCancel}>
            Cancel
          </Button>
        </Form.Item>
      </Form>
    </>
  );
}
