import { Button, Form, Input, Select } from "antd";
// import { formItemList } from "./constant";

export default function AddForm({ onFinish, onCancel }) {
  const handleFinish = (values) => {
    // dropping unused/hidden field if present
    const { allowEntryCode, ...payload } = values;
    onFinish(payload);
  };

  return (
    <Form layout="vertical" onFinish={handleFinish} initialValues={{ allowEntryCode: true }}>
      <Form.Item label='COURSE NAME' name='courseName'>
        <Input />
      </Form.Item>
      <Form.Item label='YEAR' name='year'>
        <Input />
      </Form.Item>
      <Form.Item label='SEMESTER' name='semester'>
        <Select
          options={[
            { value: "Spring" },
            { value: "Summer" },
            { value: "Fall" },
            { value: "Winter" },
          ]}
        />
      </Form.Item>
      <Form.Item label='COURSE ENTRY CODE' name='entryCode'>
        <Input />
      </Form.Item>

      {/* ensure allowEntryCode is included even without a visible field */}
      {/* while the allowEntryCode option (allowing students to enroll themselves to course) is not enabled, leaving it for 
          potential future usage */}
      <Form.Item name='allowEntryCode' initialValue={true} hidden>
        <Input type='hidden' />
      </Form.Item>
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
  );
}
