import { Alert, Button, Form, Input, Modal } from "antd";

/**
 * student relate to course window modal
 * @param {*} param0
 * @returns
 */
export default function RelationModal({ open, onCancel, onOk }) {
  return (
    <Modal
      title='Add Course via Entry Code'
      open={open}
      onCancel={onCancel}
      footer={null}
    >
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
      <Form layout='vertical' onFinish={onOk}>
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
    </Modal>
  );
}
