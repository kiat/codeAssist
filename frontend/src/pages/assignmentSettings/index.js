import { DeleteOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  DatePicker,
  Form,
  Input,
  message,
  PageHeader,
  Radio,
  Row,
  Space,
  Popconfirm,
  Select,
} from "antd";
import { useCallback, useEffect, useState } from "react";
import { useContext } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { GlobalContext } from "../../App";
import {
  deleteAssignment,
  deleteSubmissions,
  getAssignment,
  updateAssignment,
} from "../../services/assignment";
import { getCourseInfo, fetchAiModels } from "../../services/course";
import moment from "moment";
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

export default () => {
  const { assignmentId } = useParams();
  const [form] = Form.useForm();

  const [courseId, setCourseId] = useState("");
  const [publishedBefore, setPubBefore] = useState(undefined);
  const [originalPublish, setOGPub] = useState(undefined);
  const [enableAiFeedback, setEnableAiFeedback] = useState(false);

  const [courseAiInfo, setCourseAiInfo] = useState({});
  const [assignmentModels, setAssignmentModels] = useState([]);
  const [assignmentModelsLoading, setAssignmentModelsLoading] = useState(false);

  const { updateAssignmentInfo } = useContext(GlobalContext);
  const navigate = useNavigate();

  const useCourseAiDefault = Form.useWatch("use_course_ai_default", form);

  const loadCourseAiInfo = useCallback(
    async (targetCourseId) => {
      if (!targetCourseId) {
        return;
      }

      try {
        const res = await getCourseInfo({ course_id: targetCourseId });
        const course = res?.data?.[0] || {};
        setCourseAiInfo(course);
      } catch (e) {
        console.error("Failed to load course AI settings:", e);
      }
    },
    []
  );

  const getAssignmentInfo = useCallback(() => {
    getAssignment({ assignment_id: assignmentId }).then((res) => {
      const {
        name,
        published,
        due_date,
        autograder_points,
        course_id,
        published_date,
        ai_feedback_enabled,
        use_course_ai_default,
        ai_feedback_provider,
        ai_feedback_prompt,
        ai_feedback_model,
        ai_feedback_temperature,
        ai_feedback_style,
      } = res.data || {};

      setPubBefore(published);
      setOGPub(published_date);
      setCourseId(course_id);
      setEnableAiFeedback(!!ai_feedback_enabled);

      loadCourseAiInfo(course_id);

      form.setFieldsValue({
        name,
        published,
        autograderPoints: autograder_points,
        dueDate: due_date ? moment.utc(due_date).local() : null,
        releaseDate: published_date ? moment.utc(published_date).local() : null,

        enableAiFeedback: !!ai_feedback_enabled,
        use_course_ai_default: use_course_ai_default !== false,
        ai_feedback_provider: ai_feedback_provider || "openai",
        ai_feedback_prompt: ai_feedback_prompt || DEFAULT_AI_FEEDBACK_PROMPT,
        ai_feedback_model: ai_feedback_model || undefined,
        ai_feedback_temperature: ai_feedback_temperature ?? 0.5,
        ai_feedback_style: ai_feedback_style || "balanced",
      });
    });
  }, [assignmentId, form, loadCourseAiInfo]);

  useEffect(() => {
    getAssignmentInfo();
  }, [getAssignmentInfo]);

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

  const handleDeleteAssignment = async (currentAssignmentId) => {
    if (!currentAssignmentId) {
      message.error("Assignment ID is undefined");
      return;
    }

    try {
      await deleteAssignment(currentAssignmentId);
      message.success("Assignment deleted successfully");
    } catch (error) {
      console.error("Failed to delete assignment:", error);
      message.error("Failed to delete assignment");
    }
  };

  const handleDeleteSubmissions = async (currentAssignmentId) => {
    if (!currentAssignmentId) {
      message.error("Assignment ID is undefined");
      return;
    }

    try {
      await deleteSubmissions(currentAssignmentId);
      message.success("All submissions deleted successfully");
    } catch (error) {
      console.error("Failed to delete submissions:", error);
      message.error("Failed to delete submissions");
    }
  };

  const currentDate = () => {
    const current = new Date();
    return current.toISOString();
  };

  const finishForm = async () => {
    if (!assignmentId) {
      message.error("Assignment ID is missing. Cannot update.");
      return;
    }

    const values = form.getFieldsValue();

    let publishedDate = undefined;
    if (values.published === true) {
      publishedDate = publishedBefore && originalPublish ? originalPublish : currentDate();
    } else {
      publishedDate = values.releaseDate?._d || values.releaseDate;
    }

    const newAssignmentData = {
      assignment_id: assignmentId,
      name: values.name,
      course_id: courseId,
      due_date: values.dueDate?._d || values.dueDate,
      autograder_points: values.autograderPoints,
      anonymous_grading: values.submissionAnonymization,
      manual_grading: values.manualGrading,
      late_submission: values.allowLateSubmissions,
      late_due_date: values.lateDueDate,
      enable_group: values.groupSubmission,
      group_size: values.limitGroupSize,
      leaderboard: values.leaderBoard,
      published: values.published,
      published_date: publishedDate,

      ai_feedback_enabled: !!values.enableAiFeedback,
      use_course_ai_default: values.use_course_ai_default !== false,
      ai_feedback_provider:
        values.use_course_ai_default === false ? values.ai_feedback_provider : null,
      ai_feedback_model:
        values.use_course_ai_default === false ? values.ai_feedback_model : null,
      ai_feedback_prompt: values.ai_feedback_prompt ?? null,
      ai_feedback_temperature: values.ai_feedback_temperature ?? null,
      ai_feedback_style: values.ai_feedback_style ?? null,
    };

    const validData = Object.fromEntries(
      Object.entries(newAssignmentData).filter(([_, value]) => value !== undefined)
    );

    try {
      await updateAssignment(validData);
      message.success("Successfully updated assignment");

      const res = await getAssignment({ assignment_id: assignmentId });
      updateAssignmentInfo(res.data);
    } catch (err) {
      message.error("Failed to update assignment. Please try again.");
      console.error("Update error:", err);
    }
  };

  const navigateMainPage = () => {
    navigate(`/instructorDashboard/${courseId}`);
  };

  return (
    <>
      <PageHeader title="Edit Programming Assignment" />

      <Form
        layout="vertical"
        form={form}
        onFinish={async () => {
          await finishForm();
          navigateMainPage();
        }}
      >
        <Card>
          <Form.Item
            label={<span>NAME</span>}
            name="name"
            rules={[{ required: true, message: "Please enter a title" }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            label="AUTOGRADER POINTS"
            name="autograderPoints"
            rules={[{ required: true, message: "Please enter points" }]}
          >
            <Input />
          </Form.Item>

          <Form.Item label="PUBLISHED" name="published">
            <Radio.Group
              options={[
                { label: "YES", value: true },
                { label: "NO", value: false },
              ]}
            />
          </Form.Item>

          <Form.Item>
            <Row gutter={20}>
              <Col>
                <Form.Item
                  label="RELEASE DATE (CST)"
                  name="releaseDate"
                  rules={[
                    { required: true, message: "Please select a release date" },
                  ]}
                >
                  <DatePicker showTime style={{ width: "100%" }} />
                </Form.Item>

                <Form.Item name="allowLateSubmissions" valuePropName="checked">
                  <Checkbox>Allow Late Submissions</Checkbox>
                </Form.Item>
              </Col>

              <Col>
                <Form.Item
                  label="DUE DATE (CST)"
                  name="dueDate"
                  rules={[{ required: true, message: "Please select a due date" }]}
                >
                  <DatePicker showTime style={{ width: "100%" }} />
                </Form.Item>

                <Form.Item label="LATE DUE DATE (CST)" name="lateDueDate">
                  <DatePicker showTime style={{ width: "100%" }} />
                </Form.Item>
              </Col>
            </Row>
          </Form.Item>

          <Card title="AI Feedback Settings" style={{ marginBottom: 24 }}>
            <Form.Item
              label="Enable AI Feedback"
              name="enableAiFeedback"
              valuePropName="checked"
            >
              <Checkbox onChange={(e) => setEnableAiFeedback(e.target.checked)}>
                Enable AI Feedback
              </Checkbox>
            </Form.Item>

            {enableAiFeedback && (
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
                    courseAiInfo.default_ai_provider && courseAiInfo.default_ai_model
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
                        <span style={{ color: "#888", marginLeft: 8 }}>
                          {courseAiInfo.default_ai_provider || "No provider"} /{" "}
                          {courseAiInfo.default_ai_model || "No model"}
                        </span>
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
                          form.setFieldsValue({ ai_feedback_model: undefined });
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

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Save
              </Button>

              <Popconfirm
                title="Are you sure you want to delete this assignment?"
                onConfirm={() => handleDeleteAssignment(assignmentId).then(navigateMainPage)}
                okText="Yes"
                cancelText="No"
              >
                <Button danger type="primary" icon={<DeleteOutlined />}>
                  Delete Assignment
                </Button>
              </Popconfirm>

              <Popconfirm
                title="Are you sure you want to delete all submissions?"
                onConfirm={() => {
                  handleDeleteSubmissions(assignmentId);
                }}
                okText="Yes"
                cancelText="No"
              >
                <Button danger type="primary" icon={<DeleteOutlined />}>
                  Delete All Submissions
                </Button>
              </Popconfirm>
            </Space>
          </Form.Item>
        </Card>
      </Form>
    </>
  );
};