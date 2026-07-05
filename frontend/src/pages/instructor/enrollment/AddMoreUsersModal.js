import { MinusOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Form, Input, Modal } from "antd";

export default function AddMoreUsersModal({
  toggleAddMoreUsersModalOpen,
  finishMoreUsers,
  open,
}) {
  const [form] = Form.useForm();

  const handleCancel = () => {
    form.resetFields();
    toggleAddMoreUsersModalOpen();
  };

  return (
    <Modal
      title="Add more Users"
      open={open}
      onOk={() => {
        const values = form.getFieldsValue();
        finishMoreUsers(values.Email);
        form.resetFields();
      }}
      onCancel={handleCancel}
    >
      <Form form={form}>
        <Form.List name="Email" initialValue={[""]}>
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
                        <Input placeholder="Your Email" />
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
