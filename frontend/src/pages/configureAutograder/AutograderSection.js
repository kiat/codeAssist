import React from "react";
import {
  Form,
  Switch,
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
  const operation = Form.useWatch(["autograder", "operation"], form);
  const isZip = operation !== "docker";
  const zipRequired = configureNow && isZip;

  return (
    <>
      <Form.Item
        label="UPLOAD AUTOGRADER NOW"
        tooltip="Configure autograder now or skip and do it later."
      >
        <Switch checked={configureNow} onChange={setConfigureNow} />
      </Form.Item>

      {configureNow && (
        <>
          <Form.Item
            label="AUTOGRADER CONFIGURATION"
            name={["autograder", "operation"]}
          >
            <Radio.Group
              options={[
                { label: "Zip file upload", value: "zip" },
                { label: "Manual Docker Configuration", value: "docker" },
              ]}
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
                      <Button>Choose .zip</Button>
                    </Upload>
                  </Form.Item>
                </Space>
              </Form.Item>

              {/* Optional fields (no rules, no initialValue here; use parent Form.initialValues) */}
              <Form.Item label="AUTOGRADER TIMEOUT" name={["autograder", "timeout"]}>
                <Select style={{ width: 200 }}>
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
                    />
                  </Form.Item>
                </Col>
              </Row>
            </>
          ) : (
            // Docker path — optional on create
            <Form.Item
              label="DOCKERHUB IMAGE NAME"
              name={["autograder", "dockerImage"]}
              // no 'required' rule → optional at create-time
            >
              <Input placeholder="org/repo:tag" />
            </Form.Item>
          )}

          <Space>
            <Button onClick={onTestClick} disabled={!autograderFile}>
              Test Autograder
            </Button>
            <Typography.Text type="secondary">
              Testing is available after choosing a .zip.
            </Typography.Text>
          </Space>
        </>
      )}
    </>
  );
};

export default AutograderSection;
