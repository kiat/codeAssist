import { RightOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  PageHeader,
  Radio,
  Row,
  Select,
  Space,
  Typography,
  Upload,
} from "antd";
import { useCallback } from "react";
import { useState } from "react";
import PageBottom from "../../components/layout/pageBottom";
import PageContent from "../../components/layout/pageContent";
import TestAutograder from "./TestAutograder";

export default () => {
  const [modalOpen, setModalOpen] = useState(false);

  const toggleModalOpen = useCallback(() => {
    setModalOpen(t => !t);
  }, []);

  return (
    <>
      <PageContent>
        <PageHeader title='Configure Autograder'>
          <Typography.Paragraph>
            Upload your autograder code and change settings here. You can also
            come back to this step later, but submissions will not be
            automatically graded until then. Please follow our guidelines for
            structuring your autograder.
          </Typography.Paragraph>
          <Typography.Paragraph>
            Note: Uploading an autograder zip file will automatically update
            your Dockerhub image name once it is built successfully.
          </Typography.Paragraph>
        </PageHeader>
        <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
          <Form layout='vertical'>
            <Form.Item label='AUTOGRADER CONFIGURATION' name='operation'>
              <Radio.Group
                // defaultValue='0'
                options={[
                  { label: "Zip file upload", value: "0" },
                  { label: "Manual Docker Configuration", value: "1" },
                ]}
              />
            </Form.Item>
            <Form.Item
              noStyle
              shouldUpdate={(pv, cv) => pv.operation !== cv.operation}
              // dependencies={["operation"]}
            >
              {({ getFieldValue }) =>
                getFieldValue("operation") !== "1" ? (
                  <>
                    <Form.Item label='AUTOGRADER'>
                      <Space>
                        <Form.Item name='fileName' noStyle>
                          <Input disabled={true} />
                        </Form.Item>
                        <Form.Item name='uploadFile' noStyle>
                          <Upload showUploadList={false}>
                            <Button>Replace Autograder (.zip)</Button>
                          </Upload>
                        </Form.Item>
                        <Form.Item noStyle>
                          <Button>Download Autograder</Button>
                        </Form.Item>
                      </Space>
                    </Form.Item>
                    <Form.Item noStyle>
                      <Row gutter={30} style={{ width: "700px" }}>
                        <Col span={8}>
                          <Form.Item label='BASE IMAGE OS' name='baseImageOS'>
                            <Select
                              options={[
                                { label: "Ubuntu1", value: "1" },
                                { label: "Ubuntu2", value: "2" },
                              ]}
                            />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item
                            label='BASE IMAGE VESION'
                            name='baseImageVersion'
                          >
                            <Select
                              options={[
                                { label: "22.04", value: "1" },
                                { label: "22.05", value: "2" },
                              ]}
                            />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item
                            label='BASE IMAGE VARIANT'
                            name='baseImageVariant'
                          >
                            <Select
                              options={[
                                { label: "Base", value: "1" },
                                { label: "Base2", value: "2" },
                              ]}
                            />
                          </Form.Item>
                        </Col>
                      </Row>
                      <Typography.Paragraph>
                        Choose the base image that will be used to build your
                        autograder. This determines the operating system version
                        and packages available in your autograder.
                      </Typography.Paragraph>
                    </Form.Item>
                  </>
                ) : (
                  <Form.Item label='DOCKERHUB IMAGE NAME'>
                    <Input />
                  </Form.Item>
                )
              }
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type='primary'>Update Autograder</Button>
                <Button onClick={toggleModalOpen}>Test Autograder</Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      </PageContent>
      <PageBottom>
        <Button>
          <span>Manage Submissions</span>
          <RightOutlined />
        </Button>
      </PageBottom>
      <TestAutograder open={modalOpen} onCancel={toggleModalOpen} />
    </>
  );
};
