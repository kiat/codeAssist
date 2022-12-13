import { MinusOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Form, Input, Modal } from "antd";

export default function AddMoreUsersModal({ finishMoreUsers, open }) {
  const [form] = Form.useForm();
  return (
    <Modal
      title='Add more Users'
      open={open}
      onOk={() => {
        const values = form.getFieldsValue();
        // console.log("values", values);
        finishMoreUsers(values.studentIds);
      }}
    >
      <Form form={form}>
        <Form.List name='studentIds' initialValue={[""]}>
          {(fields, { add, remove }) => (
            <>
              {/* <Form.Item>
                <div style={{ display: "flex", gap: "10px" }}>
                  <Form.Item name={0} noStyle>
                    <Input placeholder='student_id' />
                  </Form.Item>
                  <Button icon={<PlusOutlined />} onClick={() => add()} />
                </div>
              </Form.Item> */}
              {fields.map((field, index) => {
                return (
                  <Form.Item key={field.key}>
                    <div
                      style={{
                        display: "flex",
                        gap: "10px",
                      }}
                    >
                      <Form.Item
                        {...field}
                        noStyle
                        name={field.name}
                        key={field.key}
                      >
                        <Input placeholder='student_id' />
                      </Form.Item>
                      {index === 0 ? (
                        <Button icon={<PlusOutlined />} onClick={() => add()} />
                      ) : (
                        <Button
                          icon={<MinusOutlined />}
                          onClick={() => remove(field.name)}
                        />
                      )}
                    </div>
                  </Form.Item>
                );
              })}
            </>
          )}
        </Form.List>
      </Form>
    </Modal>
  );
}
