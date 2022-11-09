import { Button, Form, Input, Modal } from "antd";
import { formItemList } from "./constant";

/**
 * instructor add course modal
 * @param {*} param0
 * @returns
 */
export default function AddCourseModal({ open, onCancel, onFinish }) {
  return (
    <Modal open={open} onCancel={onCancel} title='ADD COURSE' footer={null}>
      <Form layout='vertical' onFinish={onFinish}>
        {formItemList.map(item => (
          <Form.Item label={item.label} name={item.name} key={item.name}>
            <Input />
          </Form.Item>
        ))}
        <Form.Item style={{ textAlign: "center" }}>
          <Button
            type='primary'
            style={{ marginRight: "10px" }}
            htmlType='submit'
          >
            Add course
          </Button>
          <Button onClick={onCancel}>Cancel</Button>
        </Form.Item>
      </Form>
    </Modal>
  );
}
