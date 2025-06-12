import { Button, Form, Input, Select } from "antd";
// import { formItemList } from "./constant";

export default function AddForm({ onFinish, onCancel }) {


  return (
    <Form layout='vertical' onFinish={onFinish}>
      {/* {formItemList.map(item => (
        <Form.Item label={item.label} name={item.name} key={item.name}>
          <Input />
        </Form.Item>
      ))} */}
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
