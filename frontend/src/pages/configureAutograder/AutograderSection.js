import React from "react";
import {
  Form,
  Radio,
  Space,
  Input,
  Upload,
  Button,
  Select,
  Row,
  Col,
  Typography,
  message,
} from "antd";
import { FileTextOutlined } from "@ant-design/icons";

const AutograderSection = ({
  form,
  configureNow,            
  setConfigureNow,           
  autograderFile,
  setAutograderFile,
  onTestClick,
}) => {
  const operation = Form.useWatch(["autograder", "operation"], form) ?? "zip";
  const isZip = operation !== "docker";
  const disabled = !configureNow;
  const zipRequired = configureNow && isZip;

  return (
    <>
      <Form.Item
        label="CONFIGURE METHOD"
        name={["autograder", "operation"]}
      >
        <Radio.Group
          options={[
            { label: "Zip file upload", value: "zip" },
            { label: "Manual Docker Configuration", value: "docker" },
          ]}
          disabled={disabled}
        />
      </Form.Item>

      {isZip ? (
        <>
          <Form.Item label="UPLOAD AUTOGRADER (.zip)" required={zipRequired}>
            <Space>
              <Form.Item name={["autograder", "fileName"]} noStyle>
                <Input prefix={<FileTextOutlined />} disabled />
              </Form.Item>

              <Form.Item noStyle>
                <Upload
                  showUploadList={false}
                  maxCount={1}
                  disabled={disabled}
                  beforeUpload={(file) => {
                    const ok = file.name.toLowerCase().endsWith(".zip");
                    if (!ok) {
                      message.error("Autograder should be .zip");
                      return Upload.LIST_IGNORE;
                    }
                    form.setFieldValue(["autograder", "fileName"], file.name);
                    setAutograderFile(file);
                    return false; // prevent auto upload
                  }}
                >
                  <Button disabled={disabled}>Choose .zip</Button>
                </Upload>
              </Form.Item>
            </Space>
          </Form.Item>

          <Form.Item label="AUTOGRADER TIMEOUT" name={["autograder", "timeout"]}>
            <Select style={{ width: 200 }} disabled={disabled}>
              <Select.Option value="300">5 minutes</Select.Option>
              <Select.Option value="600">10 minutes</Select.Option>
              <Select.Option value="1200">20 minutes</Select.Option>
              <Select.Option value="1800">30 minutes</Select.Option>
              <Select.Option value="2400">40 minutes</Select.Option>
            </Select>
          </Form.Item>

          <Row gutter={30} style={{ maxWidth: 700 }}>
            <Col span={8}>
              <Form.Item label="BASE IMAGE OS" name={["autograder", "baseImageOS"]}>
                <Select
                  options={[{ label: "Ubuntu", value: "ubuntu" }]}
                  allowClear
                  disabled={disabled}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="BASE IMAGE VERSION" name={["autograder", "baseImageVersion"]}>
                <Select
                  options={[
                    { label: "22.04", value: "22.04" },
                    { label: "24.04", value: "24.04" },
                  ]}
                  allowClear
                  disabled={disabled}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="BASE IMAGE VARIANT" name={["autograder", "baseImageVariant"]}>
                <Select
                  options={[
                    { label: "Base", value: "base" },
                    { label: "Minimal", value: "minimal" },
                  ]}
                  allowClear
                  disabled={disabled}
                />
              </Form.Item>
            </Col>
          </Row>
        </>
      ) : (
        <Form.Item
          label="DOCKERHUB IMAGE NAME"
          name={["autograder", "dockerImage"]}
        >
          <Input placeholder="org/repo:tag" disabled={disabled} />
        </Form.Item>
      )}

      <Form.Item style={{ marginTop: 8, marginBottom: 16 }}>
        <Space size="middle">
          <Button onClick={onTestClick} disabled={disabled || !autograderFile}>
            Test Autograder
          </Button>
          <Typography.Text type="secondary">
            Testing is available after choosing a .zip.
          </Typography.Text>
        </Space>
      </Form.Item>
    </>
  );
};

export default AutograderSection;
