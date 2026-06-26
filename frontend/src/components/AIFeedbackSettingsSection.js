import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Card, Checkbox, Col, Form, Input, Row, Space, Typography } from "antd";
import { createAiFeedbackPrompt } from "../constants/aiFeedbackSettings";

const INPUT_PERMISSIONS = [
  {
    key: "assignment_description",
    label: "Assignment description",
  },
  {
    key: "student_code",
    label: "Student solution code",
  },
  {
    key: "test_results",
    label: "Test results",
  },
  {
    key: "test_cases",
    label: "Test cases",
  },
  {
    key: "student_output",
    label: "Student output",
  },
];

export default function AIFeedbackSettingsSection() {
  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <div>
        <Typography.Title level={5}>Feedback Prompts</Typography.Title>

        <Form.List name="ai_feedback_prompts">
          {(fields, { add, remove }) => (
            <Space direction="vertical" size={12} style={{ width: "100%" }}>
              {fields.map(({ key, name, ...restField }) => (
                <Card
                  key={key}
                  size="small"
                  type="inner"
                  title={
                    <Form.Item
                      {...restField}
                      name={[name, "enabled"]}
                      valuePropName="checked"
                      noStyle
                    >
                      <Checkbox>Enabled</Checkbox>
                    </Form.Item>
                  }
                  extra={
                    <Button
                      danger
                      type="text"
                      icon={<DeleteOutlined />}
                      onClick={() => remove(name)}
                      aria-label="Delete prompt"
                    />
                  }
                >
                  <Form.Item {...restField} name={[name, "id"]} hidden>
                    <Input />
                  </Form.Item>

                  <Form.Item
                    {...restField}
                    label="Prompt title"
                    name={[name, "title"]}
                    rules={[
                      {
                        required: true,
                        whitespace: true,
                        message: "Prompt title is required",
                      },
                    ]}
                  >
                    <Input placeholder="Prompt title" />
                  </Form.Item>

                  <Form.Item
                    {...restField}
                    label="Prompt instruction text"
                    name={[name, "prompt"]}
                    rules={[
                      {
                        required: true,
                        whitespace: true,
                        message: "Prompt instruction text is required",
                      },
                    ]}
                  >
                    <Input.TextArea
                      placeholder="Give the AI instructions for this feedback option"
                      autoSize={{ minRows: 3, maxRows: 8 }}
                    />
                  </Form.Item>
                </Card>
              ))}

              <Button
                icon={<PlusOutlined />}
                onClick={() => add(createAiFeedbackPrompt())}
              >
                Add Prompt
              </Button>
            </Space>
          )}
        </Form.List>
      </div>

      <div>
        <Typography.Title level={5}>AI Input Permissions</Typography.Title>

        <Row gutter={[16, 8]}>
          {INPUT_PERMISSIONS.map((permission) => (
            <Col xs={24} md={12} key={permission.key}>
              <Form.Item
                name={["ai_allowed_inputs", permission.key]}
                valuePropName="checked"
                style={{ marginBottom: 0 }}
              >
                <Checkbox>{permission.label}</Checkbox>
              </Form.Item>
            </Col>
          ))}
        </Row>
      </div>
    </Space>
  );
}
