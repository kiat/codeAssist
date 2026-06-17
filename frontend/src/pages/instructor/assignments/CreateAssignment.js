import {
  BookOutlined,
  CodeOutlined,
  FileTextOutlined,
  LeftCircleFilled,
  UploadOutlined,
} from "@ant-design/icons";
import {
  Alert,
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
  Switch,
  message,
} from "antd";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import moment from "moment";

import AutograderSection from "../../configureAutograder/AutograderSection";
import TestAutograder from "../../configureAutograder/TestAutograder";
import TestResultsDisplay from "../../result/TestResultsDisplay";
import { uploadAssignmentAutograder } from "../../../services/submission";
import { createAssignment, updateAssignment } from "../../../services/assignment";
import { getCourseInfo, fetchAiModels } from "../../../services/course";
const DEFAULT_AI_FEEDBACK_PROMPT = `You are giving short, student-facing feedback on a programming assignment.

Focus only on correctness and debugging.

Allowed feedback topics:
- Incorrect logic
- Missing required behavior
- Failed test cases
- Edge cases
- Runtime errors
- Incorrect input/output handling
- Incorrect return values
- Algorithm mistakes

Do not comment on:
- Style
- Formatting
- Naming
- Indentation
- Readability
- Refactoring

Rules:
- Do not provide corrected code.
- Do not give copy-paste fixes.
- Do not reveal the final answer.
- Give short hints that help the student investigate the bug.`;
const { Sider, Content } = Layout;

export default ({
  currentStep,
  updateCurrentStep,
  toggleIsCreate,
  nameValidationStatus,
  form,
}) => {
  const [assignmentType, setAssignmentType] = useState(0);
  const aiFeedbackEnabled = Form.useWatch("ai_feedback_enabled", form);
  const useCourseAiDefault = Form.useWatch("use_course_ai_default", form);

  const [configureAutograderNow, setConfigureAutograderNow] = useState(false);
  const [autograderFile, setAutograderFile] = useState(null);
  const [saveLoading, setSaveLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [resultsModalOpen, setResultsModalOpen] = useState(false);
  const [testResultsData, setTestResultsData] = useState(null);

  const [courseAiInfo, setCourseAiInfo] = useState({});
  const [assignmentModels, setAssignmentModels] = useState([]);
  const [assignmentModelsLoading, setAssignmentModelsLoading] = useState(false);

  const { courseId } = useParams();

  useEffect(() => {
    const loadCourseAiInfo = async () => {
      try {
        const res = await getCourseInfo({ course_id: courseId });
        const course = res?.data?.[0] || {};

        setCourseAiInfo(course);

        form.setFieldsValue({
          use_course_ai_default: true,
          ai_feedback_provider: course.default_ai_provider || "openai",
          ai_feedback_model: course.default_ai_model || undefined,
          ai_feedback_style: course.default_feedback_style || "balanced",
          ai_feedback_prompt: "",
          ai_feedback_temperature: course.default_ai_temperature ?? 0.5,
        });
      } catch (e) {
        console.error("Failed to load course AI settings:", e);
      }
    };

    if (courseId) {
      loadCourseAiInfo();
    }
  }, [courseId, form]);

  const openTest = useCallback(() => setModalOpen(true), []);
  const closeTest = useCallback(() => setModalOpen(false), []);

  const handleAutograderSuccess = (data) => {
    setTestResultsData(data);
    setResultsModalOpen(true);
  };

  const handleCloseResultsModal = () => setResultsModalOpen(false);

  const handleFetchAssignmentModels = async () => {
    const provider = form.getFieldValue("ai_feedback_provider") || "openai";

    try {
      setAssignmentModelsLoading(true);

      const response = await fetchAiModels({
        course_id: courseId,
        provider,
      });

      const fetchedModels = response?.data?.models || [];
      setAssignmentModels(fetchedModels);

      if (fetchedModels.length > 0) {
        const preferredModel = fetchedModels.includes(courseAiInfo.default_ai_model)
          ? courseAiInfo.default_ai_model
          : fetchedModels[0];

        form.setFieldsValue({
          ai_feedback_model: preferredModel,
        });
      }

      message.success("Models fetched successfully");
    } catch (e) {
      console.error("Failed to fetch models:", e.response?.data || e);
      message.error(e.response?.data?.error || "Failed to fetch models");
    } finally {
      setAssignmentModelsLoading(false);
    }
  };

  const handleFinish = async (values) => {
    try {
      setSaveLoading(true);

      if (!courseId) {
        throw new Error("Missing courseId in route. Unable to create assignment.");
      }

      const toIso = (d) => (d ? new Date(d.valueOf()).toISOString() : null);
      const now = new Date();
      const releaseDate = values.releaseDate
        ? new Date(values.releaseDate.valueOf())
        : null;

      const payload = {
        name: values.name,
        course_id: courseId,
        published_date: toIso(values.releaseDate),
        published: releaseDate ? releaseDate <= now : false,
        due_date: toIso(values.dueDate),
        late_due_date: toIso(values.lateDueDate),
        late_submission: !!values.allowLateSubmissions,
        enable_group: !!values.groupSubmission,
        group_size: values.limitGroupSize ? Number(values.limitGroupSize) : null,
        manual_grading: !!values.manualGrading,
        autograder_points: values.autograderPoints
          ? Number(values.autograderPoints)
          : null,

        ai_feedback_enabled: !!values.ai_feedback_enabled,
        use_course_ai_default: values.use_course_ai_default !== false,
        ai_feedback_provider:
          values.use_course_ai_default === false
            ? values.ai_feedback_provider
            : null,
        ai_feedback_model:
          values.use_course_ai_default === false
            ? values.ai_feedback_model
            : null,
        ai_feedback_prompt: values.ai_feedback_prompt ?? null,
        ai_feedback_temperature: values.ai_feedback_temperature ?? null,
        ai_feedback_style: values.ai_feedback_style ?? null,
      };

      const assignment = await createAssignment(payload);

      const assignmentId =
        assignment?.id ??
        assignment?.data?.id ??
        assignment?.assignment_id ??
        assignment?.data?.assignment_id;

      if (!assignmentId) {
        throw new Error("Backend did not return an assignment id.");
      }

      if (String(assignmentType) === "2" && configureAutograderNow) {
        await updateAssignment({
          assignment_id: assignmentId,
          name: values.name,
          course_id: courseId,
          autograder_points: Number(values.autograderPoints || 100),
        });

        const op = values?.autograder?.operation;

        if (op === "zip") {
          if (!autograderFile) {
            throw new Error("Please choose an autograder .zip file.");
          }

          const fd = new FormData();
          fd.append("assignment_id", assignmentId);
          fd.append("file", autograderFile);
          fd.append(
            "autograder_timeout",
            String(values?.autograder?.timeout || "300")
          );

          if (values?.autograder?.baseImageOS) {
            fd.append("base_image_os", values.autograder.baseImageOS);
            fd.append("base_image_version", values.autograder.baseImageVersion || "");
            fd.append("base_image_variant", values.autograder.baseImageVariant || "");
          }

          await uploadAssignmentAutograder(fd);
        }
      }

      message.success("Assignment created");
      form.resetFields();

      if (typeof toggleIsCreate === "function") {
        toggleIsCreate();
      }
    } catch (e) {
      console.error(e);
      message.error(e?.message || "Failed to create assignment");
    } finally {
      setSaveLoading(false);
    }
  };

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
          </Sider>

          <Content>
            <Card bordered={false}>
              <Form
                layout="vertical"
                form={form}
                initialValues={{
                  releaseDate: moment(),
                  dueDate: moment().add(7, "day"),
                  autograderPoints: "100",
                  autograder: { operation: "zip", timeout: "300" },
                  use_course_ai_default: true,
                  ai_feedback_style: "balanced",
                  ai_feedback_prompt: "",
                  ai_feedback_temperature: 0.5,
                }}
                onFinish={handleFinish}
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
                  <Form.Item label="TEMPLATE" name="template" valuePropName="fileList">
                    <Upload>
                      <Button icon={<UploadOutlined />}>select PDF</Button>
                    </Upload>
                  </Form.Item>
                ) : null}

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
                  <Form.Item label="WHO WILL UPLOAD SUBMISSIONS?" name="identify">
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
                            rules={[
                              {
                                required: true,
                                message: "Please select a release date",
                              },
                            ]}
                          >
                            <DatePicker showTime style={{ width: "100%" }} />
                          </Form.Item>
                        </Col>

                        <Col span={24} md={12}>
                          <Form.Item
                            label="DUE DATE (CDT)"
                            name="dueDate"
                            rules={[
                              {
                                required: true,
                                message: "Please select a due date",
                              },
                            ]}
                          >
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

                                  return Promise.reject(
                                    new Error("Late due date must be after due date")
                                  );
                                },
                              }),
                            ]}
                          >
                            <DatePicker showTime style={{ width: "100%" }} />
                          </Form.Item>
                        </Col>
                      </Row>
                    </Form.Item>

                    <Form.Item label="SUBMISSION TYPE" name="submissionType">
                      <Radio.Group>
                        <Space direction="vertical">
                          <Radio value={0}>Variable Length</Radio>
                          <Radio value={1}>Templated (Fixed Length)</Radio>
                        </Space>
                      </Radio.Group>
                    </Form.Item>

                    <Form.Item
                      label="GROUP SUBMISSION"
                      name="groupSubmission"
                      valuePropName="checked"
                    >
                      <Checkbox>Enable Group Submission</Checkbox>
                    </Form.Item>

                    <Form.Item
                      label="LIMIT GROUP SIZE"
                      name="limitGroupSize"
                      rules={[
                        { required: false },
                        { pattern: /^\d+$/, message: "Only numeric values allowed" },
                      ]}
                    >
                      <Input />
                    </Form.Item>

                    <Card title="AI Feedback Settings" style={{ marginBottom: 24 }}>
                      <Form.Item
                        label="Enable AI Feedback"
                        name="ai_feedback_enabled"
                        valuePropName="checked"
                      >
                        <Switch />
                      </Form.Item>

                      {aiFeedbackEnabled && (
                        <>
                          <Alert
                            type={
                              courseAiInfo.has_openai_api_key ||
                              courseAiInfo.has_gemini_api_key ||
                              courseAiInfo.has_claude_api_key
                                ? "success"
                                : "warning"
                            }
                            showIcon
                            style={{ marginBottom: 16 }}
                            message="Current Course AI Default"
                            description={
                              courseAiInfo.default_ai_provider &&
                              courseAiInfo.default_ai_model
                                ? `Using ${courseAiInfo.default_ai_provider} / ${courseAiInfo.default_ai_model} by default.`
                                : "Course default AI settings are incomplete. Configure them in Course AI Settings first."
                            }
                          />

                          <Form.Item
                            label="Model Source"
                            name="use_course_ai_default"
                            initialValue={true}
                          >
                            <Radio.Group>
                              <Space direction="vertical">
                                <Radio value={true}>
                                  Use course default
                                  <Typography.Text
                                    type="secondary"
                                    style={{ marginLeft: 8 }}
                                  >
                                    {courseAiInfo.default_ai_provider || "No provider"} /{" "}
                                    {courseAiInfo.default_ai_model || "No model"}
                                  </Typography.Text>
                                </Radio>

                                <Radio value={false}>
                                  Customize for this assignment only
                                </Radio>
                              </Space>
                            </Radio.Group>
                          </Form.Item>

                          {useCourseAiDefault === false && (
                            <Card size="small" title="Custom Assignment Model">
                              <Form.Item
                                label="Provider"
                                name="ai_feedback_provider"
                                rules={[
                                  {
                                    required: true,
                                    message: "Please select an AI provider",
                                  },
                                ]}
                              >
                                <Select
                                  options={[
                                    { label: "ChatGPT", value: "openai" },
                                    { label: "Gemini", value: "gemini" },
                                    { label: "Claude", value: "claude" },
                                  ]}
                                  onChange={() => {
                                    setAssignmentModels([]);
                                    form.setFieldsValue({
                                      ai_feedback_model: undefined,
                                    });
                                  }}
                                />
                              </Form.Item>

                              <Form.Item
                                label="Model"
                                name="ai_feedback_model"
                                rules={[
                                  {
                                    required: true,
                                    message: "Please fetch and select an AI model",
                                  },
                                ]}
                              >
                                <Space.Compact style={{ width: "100%" }}>
                                  <Button
                                    onClick={handleFetchAssignmentModels}
                                    loading={assignmentModelsLoading}
                                    style={{ width: 180 }}
                                  >
                                    Fetch Models
                                  </Button>

                                  <Select
                                    placeholder="Select a model"
                                    style={{ width: "100%" }}
                                    disabled={assignmentModels.length === 0}
                                    options={assignmentModels.map((model) => ({
                                      label: model,
                                      value: model,
                                    }))}
                                  />
                                </Space.Compact>
                              </Form.Item>
                            </Card>
                          )}

                          <Form.Item
                            label="Feedback Style"
                            name="ai_feedback_style"
                            initialValue="balanced"
                          >
                            <Select
                              options={[
                                { label: "Hint-based", value: "hint-based" },
                                { label: "Balanced", value: "balanced" },
                                { label: "Detailed debugging", value: "detailed-debugging" },
                              ]}
                            />
                          </Form.Item>

                          <Form.Item
                            label="AI Feedback Prompt"
                            name="ai_feedback_prompt"
                            initialValue=""
                          >
                            <Input.TextArea
                              placeholder="Optional. Leave blank to use the default correctness-only feedback prompt."
                              autoSize={{ minRows: 4, maxRows: 8 }}
                            />
                          </Form.Item>

                          <Form.Item
                            label="Model Temperature"
                            name="ai_feedback_temperature"
                            initialValue={0.5}
                            rules={[
                              {
                                pattern: /^0(\.\d+)?|1$/,
                                message: "Enter a value between 0 and 1",
                              },
                            ]}
                          >
                            <Input placeholder="0.5" />
                          </Form.Item>
                        </>
                      )}
                    </Card>

                    <Form.Item
                      label="CONFIGURE AUTOGRADER"
                      name="autograder_enabled"
                      valuePropName="checked"
                      initialValue={false}
                    >
                      <Switch
                        onChange={(checked) => setConfigureAutograderNow(checked)}
                      />
                    </Form.Item>

                    <AutograderSection
                      form={form}
                      configureNow={configureAutograderNow}
                      setConfigureNow={setConfigureAutograderNow}
                      autograderFile={autograderFile}
                      setAutograderFile={setAutograderFile}
                      onTestClick={openTest}
                      disabled={!configureAutograderNow}
                    />

                    <Form.Item style={{ marginBottom: 0 }} />
                  </>
                )}

                <Form.Item>
                  <Space>
                    <Button loading={saveLoading} type="primary" htmlType="submit">
                      Create Assignment
                    </Button>
                    <Button onClick={toggleIsCreate}>Cancel</Button>
                  </Space>
                </Form.Item>
              </Form>
            </Card>
          </Content>
        </Layout>
      )}

      <TestAutograder
        open={modalOpen}
        onCancel={closeTest}
        autograderFile={autograderFile}
        onSuccess={handleAutograderSuccess}
      />

      {resultsModalOpen && (
        <TestResultsDisplay
          viewMode="Results"
          assignmentName={form?.getFieldValue("name") || "Untitled Assignment"}
          studentName="John Doe"
          score={testResultsData?.score}
          totalPoints={Number(form?.getFieldValue("autograderPoints") || 100)}
          data={testResultsData}
          aiFeedbackEnabled={true}
          isModal={true}
          submissionId="dummy-id-12345"
          onCancel={handleCloseResultsModal}
        />
      )}
    </>
  );
};