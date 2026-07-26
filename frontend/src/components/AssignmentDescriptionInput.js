import { UploadOutlined } from "@ant-design/icons";
import { Button, Form, Input, message, Space, Typography, Upload } from "antd";

const MAX_DESCRIPTION_CHARS = 20000;
const MAX_DESCRIPTION_UPLOAD_BYTES = 512 * 1024;
const SUPPORTED_DESCRIPTION_EXTENSIONS = [".txt", ".md"];

function getFileExtension(fileName = "") {
  const dotIndex = fileName.lastIndexOf(".");
  return dotIndex >= 0 ? fileName.slice(dotIndex).toLowerCase() : "";
}

export default function AssignmentDescriptionInput({
  form,
  label = "ASSIGNMENT DESCRIPTION",
  name = "description",
}) {
  const description = Form.useWatch(name, form) || "";

  const readDescriptionFile = (file) => {
    const extension = getFileExtension(file.name);

    if (!SUPPORTED_DESCRIPTION_EXTENSIONS.includes(extension)) {
      message.error("Only .txt and .md files can be used for assignment descriptions.");
      return Upload.LIST_IGNORE;
    }

    if (file.size > MAX_DESCRIPTION_UPLOAD_BYTES) {
      message.error("Description files must be 512 KB or smaller.");
      return Upload.LIST_IGNORE;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || "");

      if (text.length > MAX_DESCRIPTION_CHARS) {
        message.error("Description text must be 20,000 characters or fewer.");
        return;
      }

      form.setFieldsValue({ [name]: text });
      form.validateFields([name]).catch(() => {});
      message.success("Assignment description imported.");
    };
    reader.onerror = () => {
      message.error("Could not read the selected description file.");
    };
    reader.readAsText(file);

    return Upload.LIST_IGNORE;
  };

  return (
    <>
      <Form.Item
        label={label}
        name={name}
        rules={[
          {
            max: MAX_DESCRIPTION_CHARS,
            message: "Description must be 20,000 characters or fewer",
          },
        ]}
      >
        <Input.TextArea
          rows={6}
          maxLength={MAX_DESCRIPTION_CHARS}
          showCount
          placeholder="Enter assignment requirements, input/output format, constraints, and grading expectations."
        />
      </Form.Item>

      <Space style={{ marginTop: -16, marginBottom: 24 }} wrap>
        <Upload
          accept=".txt,.md,text/plain,text/markdown"
          beforeUpload={readDescriptionFile}
          showUploadList={false}
        >
          <Button icon={<UploadOutlined />}>Upload .txt or .md</Button>
        </Upload>

        <Typography.Text type="secondary">
          {String(description).length}/{MAX_DESCRIPTION_CHARS}
        </Typography.Text>
      </Space>
    </>
  );
}
