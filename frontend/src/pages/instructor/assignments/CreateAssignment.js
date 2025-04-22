import {
  BookOutlined,
  CodeOutlined,
  FileTextOutlined,
  LeftCircleFilled,
  UploadOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Checkbox,
  Col,
  DatePicker,
  Form,
  Input,
  Layout,
  Menu,
  Radio,
  Row,
  Space,
  Steps,
  Typography,
  Upload,
  Select,
  Switch
} from "antd";
import { useState } from "react";
import dayjs from "dayjs";


const { Sider, Content } = Layout;

export default ({
  currentStep,
  updateCurrentStep,
  toggleIsCreate,
  nameValidationStatus,
  form,
}) => {
  const [assignmentType, setAssignmentType] = useState(0);
  const [enableAiFeedback, setEnableAiFeedback] = useState(true);
  const aiFeedbackEnabled = Form.useWatch("ai_feedback_enabled", form);


  return (
    <>
      <Steps
        current={currentStep}
        type="navigation"
        items={[
          { title: "Assignment Type", status: "process" },
          { title: "Assignment Settings", status: "process" },
        ]}
      />
      {currentStep === 0 ? (
        <Card bordered={false}>
          <Typography.Link onClick={toggleIsCreate}>
            <LeftCircleFilled />
            <span> Exit</span>
          </Typography.Link>
          <Typography.Title level={5}>ASSIGNMENT TYPES</Typography.Title>
          <Menu
            onClick={({ key }) => {
              setAssignmentType(key);
              updateCurrentStep(1);
            }}
            items={[
              // {
              //   label: "Exam / Quiz",
              //   key: 0,
              //   icon: <FileTextOutlined />,
              // },
              // {
              //   label: "Homework / Problem Set",
              //   key: 1,
              //   icon: <BookOutlined />,
              // },
              {
                label: "Programming Assignment",
                key: 2,
                icon: <CodeOutlined />,
              },
            ]}
          />
        </Card>
      ) : (
        <Layout>
          <Sider theme="light" width={230}>
            <Card bordered={false}>
              {/* <Typography.Text level={5}>
              <LeftCircleFilled />
              <span> Go Back</span>
            </Typography.Text> */}
              <Typography.Link
                onClick={() => {
                  setAssignmentType("");
                  updateCurrentStep(0);
                }}
              >
                <LeftCircleFilled />
                <span> Go Back</span>
              </Typography.Link>
              <Typography.Title level={5}>ASSIGNMENT TYPE</Typography.Title>
              {assignmentType === "0" ? (
                <div>
                  <FileTextOutlined />
                  <span> Exam / Quiz</span>
                </div>
              ) : assignmentType === "1" ? (
                <div>
                  <BookOutlined />
                  <span> Homework / Problem Set</span>
                </div>
              ) : (
                <div>
                  <CodeOutlined />
                  <span> Programming Assignment</span>
                </div>
              )}
            </Card>
            {/* <Menu
            items={[
              { label: "Exam/Quiz" },
              { label: "Homework/Problem Set" },
              { label: "Programing Assignment" },
            ]}
          /> */}
          </Sider>
          <Content>
            <Card bordered={false}>
              <Form layout="vertical" form={form}
                initialValues={{
                  releaseDate: dayjs(), // current date
                  dueDate: dayjs().add(7, "day"), // 7 days from now
                  autograderPoints: "100",
                }}
                >
                <Form.Item
                  label="ASSIGNMENT NAME"
                  name="name"
                  validateStatus={nameValidationStatus}
                  rules={[{ required: true, message: "Please enter a name" }]}
                >
                  <Input placeholder="Name your assignment" />
                </Form.Item>
                {assignmentType !== "2" ? (
                  <Form.Item
                    label="TEMPLATE"
                    name="template"
                    valuePropName="fileList"
                  >
                    <Upload>
                      <Button icon={<UploadOutlined />}>select PDF</Button>
                    </Upload>
                  </Form.Item>
                ) : null}
                 {/* <Form.Item
                  label="SUBMISSION ANONYMIZATION"
                  name="submissionAnonymization"
                  valuePropName="checked"
                >
                  <Checkbox>Enable Anonymous Grading</Checkbox>
                </Form.Item> */}
                {assignmentType === "2" ? (
                  <>
                    <Form.Item
                      label="AUTOGRADER POINTS"
                      name="autograderPoints"
                      rules={[
                        { required: true, message: "Please enter a point value" },
                        { pattern: /^\d+$/, message: "Only numeric values allowed" },
                      ]}
                    >
                      <Input />
                    </Form.Item>
                    <Form.Item
                      label="MANUAL GRADING"
                      name="manualGrading"
                      valuePropName="checked"
                    >
                      <Checkbox>Enable Manual Grading</Checkbox>
                    </Form.Item>
                  </>
                ) : (
                  <Form.Item
                    label="WHO WILL UPLOAD SUBMISSIONS?"
                    name="identify"
                  >
                    <Radio.Group options={["Instructor", "Student"]} />
                  </Form.Item>
                )}

                {assignmentType === "0" ? null : (
                  <>
                    <Form.Item wrapperCol={{ xl: 12 }}>
                      <Row gutter={20}>
                        <Col span={24} md={12}>
                          <Form.Item
                            label="RELEASE DATE (CDT)"
                            name="releaseDate"
                            rules={[{ required: true, message: "Please select a release date" }]}
                          >
                            <DatePicker showTime style={{ width: "100%" }} />
                          </Form.Item>
                        </Col>
                        <Col span={24} md={12}>
                          <Form.Item label="DUE DATE (CDT)" name="dueDate" rules={[{ required: true, message: "Please select a due date" }]}>
                            <DatePicker showTime style={{ width: "100%" }} />
                          </Form.Item>
                        </Col>
                        <Col span={24} md={12}>
                          <Form.Item
                            name="allowLateSubmissions"
                            valuePropName="checked"
                          >
                            <Checkbox>Allow Late Submissions</Checkbox>
                          </Form.Item>
                        </Col>
                        <Col span={24} md={12}>
                          <Form.Item
                            label="LATE DUE DATE (CDT)"
                            dependencies={["dueDate"]}
                            name="lateDueDate"
                            rules={[
                              ({ getFieldValue }) => ({
                                validator(_, value) {
                                  if (!value || getFieldValue("dueDate") < value) {
                                    return Promise.resolve();
                                  }
                                  return Promise.reject(new Error("Late due date must be after due date"));
                                },
                              }),
                            ]}
                          >
                            <DatePicker showTime style={{ width: "100%" }} />
                          </Form.Item>
                        </Col>
                        {assignmentType === "1" ? (
                          <>
                            <Col span={24} md={12}>
                              <Form.Item
                                name="enforceTimeLimit"
                                valuePropName="checked"
                              >
                                <Checkbox>Enforce time limit</Checkbox>
                              </Form.Item>
                            </Col>
                            <Col span={24} md={12}>
                              <Form.Item
                                label="MAXIMUM TIME PERMITTED (MINUTES)"
                                name="maximumTimePermitted"
                              >
                                <DatePicker
                                  showTime
                                  style={{ width: "100%" }}
                                />
                              </Form.Item>
                            </Col>
                          </>
                        ) : null}
                      </Row>
                    </Form.Item>
                    {assignmentType === "2" ? null : (
                      <Form.Item label="SUBMISSION TYPE" name="submissionType">
                        <Radio.Group>
                          <Space direction="vertical">
                            <Radio value={0}>Variable Length</Radio>
                            <Radio value={1}>Templated (Fixed Length)</Radio>
                          </Space>
                        </Radio.Group>
                      </Form.Item>
                    )}
                    <Form.Item
                      label="GROUP SUBMISSION"
                      name="groupSubmission"
                      valuePropName="checked"
                    >
                      <Checkbox>Enable Group Submission</Checkbox>
                    </Form.Item>
                    <Form.Item label="LIMIT GROUP SIZE" 
                    name="limitGroupSize" 
                    rules={[
                      { required: false},
                      { pattern: /^\d+$/, message: "Only numeric values allowed" },
                    ]}>
                      <Input />
                    </Form.Item>

                {/* AI Feedback Toggle */}
                <Form.Item
                  label="ENABLE AI FEEDBACK"
                  name="ai_feedback_enabled"
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>

                {/* AI Feedback Settings (Disabled when switch is off) */}
                <Form.Item
                  label="AI FEEDBACK PROMPT"
                  name="ai_feedback_prompt"
                  initialValue={"You are an AI used to provide constructive feedback to students on their coding assignments. Provide feedback on the following assignment regarding correctness, efficiency, code quality, documentation, error handling, style/formatting."}
                  rules={[{ required: aiFeedbackEnabled, message: "Please enter a feedback prompt" }]}
                >
                  <Input.TextArea
                    placeholder="Enter the feedback prompt for AI"
                    autoSize={{ minRows: 4, maxRows: 8 }}
                    disabled={!aiFeedbackEnabled}
                  />
                </Form.Item>

                <Form.Item
                  label="AI MODEL USED"
                  name="ai_feedback_model"
                  initialValue="gpt-4o"
                  rules={[{ required: aiFeedbackEnabled, message: "Please select an AI model" }]}
                >
                  <Select placeholder="Select AI model" disabled={!aiFeedbackEnabled}>
                    <Select.Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Select.Option>
                    <Select.Option value="gpt-4o">GPT-4o</Select.Option>
                    <Select.Option value="custom-model">Custom Model</Select.Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  label="MODEL TEMPERATURE"
                  name="ai_feedback_temperature"
                  initialValue={0.5}
                  rules={[
                    { required: aiFeedbackEnabled, message: "Please enter a temperature" },
                    { pattern: /^0(\.\d+)?|1$/, message: "Enter a value between 0 and 1" },
                  ]}
                >
                  <Input placeholder="Enter temperature (0 to 1)" disabled={!aiFeedbackEnabled} />
                </Form.Item>

                  </>
                )}
                {/* {assignmentType === "2" ? (
                  <>
                    <Form.Item
                      label="LEADERBOARD"
                      name="leaderBoard"
                      valuePropName="checked"
                    >
                      <Checkbox>Enable Leaderboard</Checkbox>
                    </Form.Item>
                    <Form.Item label="DEFAULT # OF ENTRIES" name="leaderBoard" rules={[
                      { required: false},
                      { pattern: /^\d+$/, message: "Only numeric values allowed" },
                    ]}>
                      <Input />
                    </Form.Item>
                  </>
                ) : (
                  <Form.Item label="CREATE YOUR RUBRIC" name="rubric">
                    <Radio.Group
                      options={[
                        { label: "Before student submission", value: 0 },
                        { label: "while grading submissions", value: 1 },
                      ]}
                    />
                  </Form.Item>
                )}
                {assignmentType === "1" ? (
                  <Form.Item
                    label="TEMPLATE VISIBILITY"
                    name="templateVisibility"
                    valuePropName="checked"
                  >
                    <Checkbox>
                      Allow student to view and download the template
                    </Checkbox>
                  </Form.Item>
                ) : null} */}
              </Form>
            </Card>
          </Content>
        </Layout>
      )}
    </>
  );
};