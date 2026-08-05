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
  Switch,
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
import AIFeedbackSettingsSection from "../../components/AIFeedbackSettingsSection";
import { ASSIGNMENT_DATE_TIME_PICKER_PROPS } from "../../constants/dateTimePicker";
import {
  normalizeAiAllowedInputs,
  normalizeAiFeedbackPrompts,
} from "../../constants/aiFeedbackSettings";

export default () => {
  const { assignmentId } = useParams();
  const [form] = Form.useForm();

  const [courseId, setCourseId] = useState("");
  const [publishedBefore, setPubBefore] = useState(undefined);
  const [originalPublish, setOGPub] = useState(undefined);
  const [enableAiFeedback, setEnableAiFeedback] = useState(false);
  const [allowLateSubmissions, setAllowLateSubmissions] = useState(false);
  
  const [courseAiInfo, setCourseAiInfo] = useState({});
  const [assignmentModels, setAssignmentModels] = useState([]);
  const [assignmentModelsLoading, setAssignmentModelsLoading] = useState(false);

  const { updateAssignmentInfo } = useContext(GlobalContext);
  const navigate = useNavigate();

  const useCourseAiDefault = Form.useWatch("use_course_ai_default", form);

  useEffect(() => {
    if (enableAiFeedback && !form.getFieldValue("ai_feedback_prompts")) {
      form.setFieldsValue({
        ai_feedback_prompts: normalizeAiFeedbackPrompts(),
        ai_allowed_inputs: normalizeAiAllowedInputs(),
      });
    }
  }, [enableAiFeedback, form]);

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
        late_submission,
        late_due_date,
        allow_file_upload,
        enable_code_editor,
        ai_feedback_enabled,
        use_course_ai_default,
        ai_feedback_provider,
        ai_feedback_prompt,
        ai_feedback_prompts,
        ai_allowed_inputs,
        ai_feedback_model,
        ai_feedback_temperature,
        ai_feedback_style,
        ai_feedback_max_requests,
        ai_feedback_wait_seconds,
        has_assignment_ai_key,
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
        allowLateSubmissions: !!late_submission,
        lateDueDate: late_due_date ? moment.utc(late_due_date).local() : null,
        allow_file_upload: allow_file_upload !== false,
        enable_code_editor: !!enable_code_editor,
        enableAiFeedback: !!ai_feedback_enabled,
        use_course_ai_default: use_course_ai_default !== false,
        ai_feedback_provider: ai_feedback_provider || "openai",
        ai_feedback_prompts: normalizeAiFeedbackPrompts(
          ai_feedback_prompts,
          ai_feedback_prompt
        ),
        ai_allowed_inputs: normalizeAiAllowedInputs(ai_allowed_inputs),
        ai_feedback_model: ai_feedback_model || undefined,
        ai_feedback_temperature: ai_feedback_temperature ?? 0.5,
        ai_feedback_style: ai_feedback_style || "balanced",
        ai_feedback_max_requests: ai_feedback_max_requests ?? null,
        ai_feedback_wait_seconds: ai_feedback_wait_seconds ?? 0,
        has_assignment_ai_key: !!has_assignment_ai_key,
        ai_feedback_api_key: "",
      });
      setAllowLateSubmissions(late_submission);
    });
  }, [assignmentId, form, loadCourseAiInfo]);

  useEffect(() => {
    getAssignmentInfo();
  }, [getAssignmentInfo]);

  const handleFetchAssignmentModels = async () => {
    const provider = form.getFieldValue("ai_feedback_provider") || "openai";
    const assignmentApiKey = (
      form.getFieldValue("ai_feedback_api_key") || ""
    ).trim();

    try {
      setAssignmentModelsLoading(true);

      const fetchPayload = {
        course_id: courseId,
        provider,
      };
      if (assignmentApiKey) {
        fetchPayload.api_key = assignmentApiKey;
      }

      const response = await fetchAiModels(fetchPayload);

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

      message.success("Models refreshed successfully");
    } catch (e) {
      console.error("Failed to fetch models:", e.response?.data || e);
      message.error(e.response?.data?.error || "Failed to refresh models");
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
    const feedbackPrompts = normalizeAiFeedbackPrompts(
      values.ai_feedback_prompts,
      values.ai_feedback_prompt
    );
    const firstPrompt =
      feedbackPrompts.find((prompt) => prompt.enabled) || feedbackPrompts[0];

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
      late_due_date: values.allowLateSubmissions ? values.lateDueDate : null,
      allow_file_upload: values.allow_file_upload !== false,
      enable_code_editor: !!values.enable_code_editor,
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
      ...(values.use_course_ai_default === false &&
      (values.ai_feedback_api_key || "").trim()
        ? { ai_feedback_api_key: values.ai_feedback_api_key.trim() }
        : {}),
      ai_feedback_prompt: firstPrompt?.prompt ?? null,
      ai_feedback_prompts: feedbackPrompts,
      ai_allowed_inputs: normalizeAiAllowedInputs(values.ai_allowed_inputs),
      ai_feedback_temperature: values.ai_feedback_temperature ?? null,
      ai_feedback_style: values.ai_feedback_style ?? null,
      ai_feedback_max_requests: values.ai_feedback_max_requests ?? null,
      ai_feedback_wait_seconds: values.ai_feedback_wait_seconds ?? 0,
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

          <Form.Item label="SUBMISSION METHODS" style={{ marginBottom: 4 }} />

          <Form.Item
            label="Allow File Upload"
            name="allow_file_upload"
            valuePropName="checked"
            tooltip="Allow students to upload a file as their submission"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            label="Enable Code Editor"
            name="enable_code_editor"
            valuePropName="checked"
            tooltip="Allow students to write and submit code directly in the browser"
          >
            <Switch />
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
                  <DatePicker {...ASSIGNMENT_DATE_TIME_PICKER_PROPS} />
                </Form.Item>
                <Form.Item name="allowLateSubmissions" valuePropName="checked">
                  <Checkbox onChange={(e) => setAllowLateSubmissions(e.target.checked)}>
                    Allow Late Submissions
                  </Checkbox>
                </Form.Item>
              </Col>

              <Col>
                <Form.Item
                  label="DUE DATE (CST)"
                  name="dueDate"
                  rules={[{ required: true, message: "Please select a due date" }]}
                >
                  <DatePicker {...ASSIGNMENT_DATE_TIME_PICKER_PROPS} />
                </Form.Item>
                {allowLateSubmissions && (
                  <Form.Item label='LATE DUE DATE (CST)' name='lateDueDate'>
                    <DatePicker {...ASSIGNMENT_DATE_TIME_PICKER_PROPS} />
                  </Form.Item>
                )}
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
                    courseAiInfo.has_claude_api_key ||
                    courseAiInfo.has_ollama_api_key
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
                          { label: "Ollama (Local LLM)", value: "ollama" },
                        ]}
                        onChange={() => {
                          setAssignmentModels([]);
                          form.setFieldsValue({
                            ai_feedback_model: undefined,
                            ai_feedback_api_key: "",
                          });
                        }}
                      />
                    </Form.Item>

                    <Form.Item shouldUpdate noStyle>
                      {({ getFieldValue }) => (
                        <>
                          {getFieldValue("has_assignment_ai_key") && (
                            <Alert
                              type="info"
                              showIcon
                              style={{ marginBottom: 16 }}
                              message="Assignment credential saved"
                              description="Paste a new value only when replacing it. Switching back to course defaults will clear the saved assignment credential."
                            />
                          )}

                          <Form.Item
                            label="Assignment API Key / Base URL"
                            name="ai_feedback_api_key"
                          >
                            <Input.Password
                              autoComplete="new-password"
                              placeholder="Use a custom credential for this assignment"
                            />
                          </Form.Item>
                        </>
                      )}
                    </Form.Item>

                    <Form.Item
                      label="Model"
                      name="ai_feedback_model"
                      rules={[
                        {
                          required: true,
                          message: "Please refresh and select an AI model",
                        },
                      ]}
                    >
                      <Space.Compact style={{ width: "100%" }}>
                        <Button
                          onClick={handleFetchAssignmentModels}
                          loading={assignmentModelsLoading}
                          style={{ width: 180 }}
                        >
                          Refresh Models
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

              <AIFeedbackSettingsSection />

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
