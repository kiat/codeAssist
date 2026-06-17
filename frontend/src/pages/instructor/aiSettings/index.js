import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  KeyOutlined,
  RobotOutlined,
} from "@ant-design/icons";

import {
  Alert,
  Button,
  Card,
  Divider,
  Form,
  Input,
  Layout,
  Menu,
  PageHeader,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from "antd";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  getCourseInfo,
  updateAiSettings,
  fetchAiModels,
  testAiModel,
} from "../../../services/course";

const { Sider, Content } = Layout;

const PROVIDERS = [
  { key: "openai", label: "ChatGPT", displayName: "OpenAI / ChatGPT" },
  { key: "gemini", label: "Gemini", displayName: "Google Gemini" },
  { key: "claude", label: "Claude", displayName: "Anthropic Claude" },
];

const FEEDBACK_STYLES = [
  { label: "Hint-based", value: "hint-based" },
  { label: "Balanced", value: "balanced" },
  { label: "Detailed debugging", value: "detailed-debugging" },
];
const PROVIDER_DEFAULT_MODELS = {
  openai: "gpt-4o-mini",
  gemini: "gemini-1.5-flash",
  claude: "claude-3-5-sonnet-20241022",
};

export default function AISettings() {
  const { courseId } = useParams();
  const [form] = Form.useForm();

  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [modelName, setModelName] = useState("");
  const [models, setModels] = useState([]);
  const [courseAiInfo, setCourseAiInfo] = useState({});
  const [isTesting, setIsTesting] = useState(false);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [apiTestStatus, setApiTestStatus] = useState(null);

  const selectedProvider = PROVIDERS.find((item) => item.key === provider);

  const getKeyStatus = (course, selectedProviderKey) => {
    if (selectedProviderKey === "openai") {
      return !!course.has_openai_api_key;
    }
    if (selectedProviderKey === "gemini") {
      return !!course.has_gemini_api_key;
    }
    if (selectedProviderKey === "claude") {
      return !!course.has_claude_api_key;
    }
    return false;
  };

  const getProviderKeyValue = (course, selectedProviderKey) => {
    if (selectedProviderKey === "openai") {
      return course.openai_api_key_value || "";
    }

    if (selectedProviderKey === "gemini") {
      return course.gemini_api_key_value || "";
    }

    if (selectedProviderKey === "claude") {
      return course.claude_api_key_value || "";
    }

    return "";
  };
  const loadCourseAiInfo = async () => {
    try {
      const res = await getCourseInfo({ course_id: courseId });
      const course = res?.data?.[0] || {};

      setCourseAiInfo(course);

      const defaultProvider = course.default_ai_provider || "openai";
      const defaultModel =
        course.default_ai_model ||
        PROVIDER_DEFAULT_MODELS[defaultProvider] ||
        "";

      setProvider(defaultProvider);
      setModelName(defaultModel);
      setApiKey(getProviderKeyValue(course, defaultProvider));

      form.setFieldsValue({
        provider: defaultProvider,
        model_name: defaultModel,
        feedback_style: course.default_feedback_style || "balanced",
        temperature: course.default_ai_temperature ?? 0.5,
      });
    } catch (e) {
      console.error("Failed to load course AI settings:", e);
      message.error("Failed to load AI settings");
    }
  };
  useEffect(() => {
    loadCourseAiInfo();
  }, [courseId]);

  const handleProviderChange = (newProvider) => {
    setProvider(newProvider);
    setModels([]);
    setApiTestStatus(null);

    const savedKey = getProviderKeyValue(courseAiInfo, newProvider);
    const fallbackModel = PROVIDER_DEFAULT_MODELS[newProvider] || "";

    setApiKey(savedKey);

    if (newProvider === courseAiInfo.default_ai_provider) {
      const savedModel = courseAiInfo.default_ai_model || fallbackModel;

      setModelName(savedModel);
      form.setFieldsValue({
        provider: newProvider,
        model_name: savedModel,
      });
    } else {
      setModelName(fallbackModel);
      form.setFieldsValue({
        provider: newProvider,
        model_name: fallbackModel,
      });
    }
  };

  const handleFetchModels = async () => {
    try {
      setModelsLoading(true);

      const response = await fetchAiModels({
        course_id: courseId,
        provider,
        api_key: apiKey || undefined,
      });

      const fetchedModels = response?.data?.models || [];
      setModels(fetchedModels);

      if (fetchedModels.length === 0) {
        message.warning("No models found for this provider");
        return;
      }

      const providerPreferredModel = PROVIDER_DEFAULT_MODELS[provider];

      const preferredModel =
        providerPreferredModel && fetchedModels.includes(providerPreferredModel)
          ? providerPreferredModel
          : fetchedModels[0];

      if (!modelName || !fetchedModels.includes(modelName)) {
        setModelName(preferredModel);
        form.setFieldsValue({ model_name: preferredModel });
      }

      message.success("Models fetched successfully");
    } catch (e) {
      console.error("Failed to fetch models:", e.response?.data || e);
      message.error(e.response?.data?.error || "Failed to fetch models");
    } finally {
      setModelsLoading(false);
    }
  };

  const testConnection = async () => {
    try {
      setIsTesting(true);
      setApiTestStatus(null);

      const values = form.getFieldsValue();
      const selectedModel = values.model_name || modelName;

      if (!selectedModel) {
        message.error("Please fetch models and select a model before testing");
        setApiTestStatus("error");
        return;
      }

      await testAiModel({
        course_id: courseId,
        provider,
        model: selectedModel,
        api_key: apiKey || undefined,
      });

      setApiTestStatus("success");
      message.success("Selected model can be used successfully");
    } catch (e) {
      console.error("Selected model test failed:", e.response?.data || e);
      setApiTestStatus("error");
      message.error(
        e.response?.data?.error ||
          "Selected model cannot be used. Please fetch models and choose another model."
      );
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      await updateAiSettings({
        course_id: courseId,
        provider,
        model_name: values.model_name,
        api_key: apiKey || undefined,
        feedback_style: values.feedback_style,
        temperature: values.temperature,
      });

      message.success("Course AI settings saved");
      await loadCourseAiInfo();
    } catch (e) {
      console.error("Failed to save AI settings:", e.response?.data || e);
      message.error(e.response?.data?.error || "Failed to save AI settings");
    }
  };

  const hasSavedKey = getKeyStatus(courseAiInfo, provider);
  const setupReady = hasSavedKey && !!modelName;

  return (
    <Layout style={{ background: "#fff", minHeight: "100%" }}>
      <Sider
        width={260}
        style={{ background: "#fff", borderRight: "1px solid #f0f2f5" }}
      >
        <div style={{ padding: "16px" }}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            AI Providers
          </Typography.Title>
          <Typography.Text type="secondary">
            Select a provider to configure.
          </Typography.Text>
        </div>

        <Menu
          mode="inline"
          selectedKeys={[provider]}
          onClick={(item) => handleProviderChange(item.key)}
          items={PROVIDERS.map((item) => ({
            key: item.key,
            label: item.label,
          }))}
        />
      </Sider>

      <Content style={{ padding: "0 24px 24px" }}>
        <Form form={form} layout="vertical">
          <Space direction="vertical" style={{ width: "100%" }} size="large">
            <PageHeader
              title="AI Settings"
              subTitle="Configure course default AI settings and provider keys"
            />

            <Card title="AI Setup Status">
              <Space direction="vertical" style={{ width: "100%" }}>
                <Space>
                  {setupReady ? (
                    <Tag color="success" icon={<CheckCircleOutlined />}>
                      Ready
                    </Tag>
                  ) : (
                    <Tag color="warning" icon={<CloseCircleOutlined />}>
                      Setup incomplete
                    </Tag>
                  )}

                  <Typography.Text>
                    Default:{" "}
                    <strong>
                      {courseAiInfo.default_ai_provider || "Not selected"} /{" "}
                      {courseAiInfo.default_ai_model || "No model selected"}
                    </strong>
                  </Typography.Text>
                </Space>

                {!hasSavedKey && (
                  <Alert
                    type="warning"
                    showIcon
                    message={`${selectedProvider?.label} API key is not saved`}
                    description="Add and save an API key before using this provider for AI feedback."
                  />
                )}
              </Space>
            </Card>

            <Card
              title={
                <Space>
                  <RobotOutlined />
                  <span>Course Default Model</span>
                </Space>
              }
            >
              <Typography.Paragraph type="secondary">
                This provider and model will be used by assignments unless an
                assignment chooses custom AI settings.
              </Typography.Paragraph>

              <Alert
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
                message="Fetch models before choosing"
                description="Click Fetch Models first to load all available models for this provider. Before fetching, the dropdown may only show the currently saved/default model."
              />

              <Form.Item label="Provider" name="provider">
                <Select
                  value={provider}
                  onChange={handleProviderChange}
                  options={PROVIDERS.map((item) => ({
                    label: item.displayName,
                    value: item.key,
                  }))}
                />
              </Form.Item>

              <Form.Item
                label="Default Model"
                name="model_name"
                rules={[
                  {
                    required: true,
                    message: "Please fetch models and select a usable model",
                  },
                ]}
              >
                <Space.Compact style={{ width: "100%" }}>
                  <Button
                    onClick={handleFetchModels}
                    loading={modelsLoading}
                    style={{ width: 180 }}
                  >
                    Fetch Models
                  </Button>

                  <Select
                    value={modelName || undefined}
                    onChange={(value) => {
                      setModelName(value);
                      form.setFieldsValue({ model_name: value });
                    }}
                    placeholder="Select a model"
                    style={{ width: "100%" }}
                    disabled={models.length === 0 && !modelName}
                    options={[
                      ...(modelName
                        ? [{ label: modelName, value: modelName }]
                        : []),
                      ...models
                        .filter((item) => item !== modelName)
                        .map((item) => ({
                          label: item,
                          value: item,
                        })),
                    ]}
                  />
                </Space.Compact>
              </Form.Item>
            </Card>

            <Card
              title={
                <Space>
                  <KeyOutlined />
                  <span>Provider API Key</span>
                </Space>
              }
            >
              <Space direction="vertical" style={{ width: "100%" }}>
                <Alert
                  type={hasSavedKey ? "success" : "info"}
                  showIcon
                  message={
                    hasSavedKey
                      ? `${selectedProvider?.label} API key is saved`
                      : `${selectedProvider?.label} API key is not configured`
                  }
                  description={
                    hasSavedKey
                      ? "Saved key is loaded into the password field and hidden by default. Use the visibility icon to view it."
                      : "Paste an API key below and save it for this provider."
                  }
                />

                <Form.Item label="Add or Replace API Key">
                  <Input.Password
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Paste a new API key to add or replace"
                    visibilityToggle
                  />
                </Form.Item>

                <Space>
                  <Button onClick={testConnection} disabled={isTesting}>
                    Test Connection
                  </Button>

                  {isTesting && (
                    <Spin
                      indicator={
                        <LoadingOutlined style={{ fontSize: 16 }} spin />
                      }
                    />
                  )}

                  {apiTestStatus === "success" && (
                    <Typography.Text type="success">
                      <CheckCircleOutlined /> Connected successfully
                    </Typography.Text>
                  )}

                  {apiTestStatus === "error" && (
                    <Typography.Text type="danger">
                      <CloseCircleOutlined /> Connection failed
                    </Typography.Text>
                  )}
                </Space>
              </Space>
            </Card>

            <Card title="Feedback Defaults">
              <Form.Item label="Feedback Style" name="feedback_style">
                <Select options={FEEDBACK_STYLES} />
              </Form.Item>

              <Form.Item
                label="Temperature"
                name="temperature"
                rules={[
                  {
                    pattern: /^0(\.\d+)?|1$/,
                    message: "Enter a value between 0 and 1",
                  },
                ]}
              >
                <Input placeholder="0.5" />
              </Form.Item>
            </Card>

            <Divider />

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <Button type="primary" onClick={handleSave}>
                Save Course Default
              </Button>
            </div>
          </Space>
        </Form>
      </Content>
    </Layout>
  );
}