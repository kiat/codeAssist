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
import { useCallback, useContext, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { GlobalContext } from "../../../App";
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
  { key: "ollama", label: "Ollama", displayName: "Ollama (Local LLM)" },
];

const FEEDBACK_STYLES = [
  { label: "Hint-based", value: "hint-based" },
  { label: "Balanced", value: "balanced" },
  { label: "Detailed debugging", value: "detailed-debugging" },
];

const PROVIDER_DEFAULT_MODELS = {
  openai: "gpt-4o",
  gemini: "gemini-1.5-flash",
  claude: "claude-3-5-sonnet-20241022",
  ollama: "llama3",
};

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
  if (selectedProviderKey === "ollama") {
    return !!course.has_ollama_api_key;
  }
  return false;
};

export default function AISettings() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { userInfo, courseRole } = useContext(GlobalContext);
  const [form] = Form.useForm();

  useEffect(() => {
    if (courseRole && courseRole !== "instructor") {
      navigate(`/instructorDashboard/${courseId}`);
    }
  }, [courseRole, courseId, navigate]);

  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [modelName, setModelName] = useState("");
  const [models, setModels] = useState([]);
  const [courseAiInfo, setCourseAiInfo] = useState({});
  const [isTesting, setIsTesting] = useState(false);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [apiTestStatus, setApiTestStatus] = useState(null);

  const selectedProvider = PROVIDERS.find((item) => item.key === provider);
  const isOllama = provider === "ollama";
  const hasSavedKey = getKeyStatus(courseAiInfo, provider);

  const fetchModelsForProvider = useCallback(
    async ({
      targetProvider,
      keyOverride = "",
      currentModel = "",
      silent = false,
    } = {}) => {
      try {
        setModelsLoading(true);

        const response = await fetchAiModels({
          course_id: courseId,
          provider: targetProvider,
          api_key: keyOverride || undefined,
        });

        const fetchedModels = response?.data?.models || [];
        setModels(fetchedModels);

        if (fetchedModels.length === 0) {
          if (!silent) {
            message.warning("No models found for this provider");
          }
          return;
        }

        const providerPreferredModel = PROVIDER_DEFAULT_MODELS[targetProvider];

        const preferredModel =
          providerPreferredModel && fetchedModels.includes(providerPreferredModel)
            ? providerPreferredModel
            : fetchedModels[0];

        if (!currentModel || !fetchedModels.includes(currentModel)) {
          setModelName(preferredModel);
          form.setFieldsValue({ model_name: preferredModel });
        }

        if (!silent) {
          message.success("Models refreshed successfully");
        }
      } catch (e) {
        console.error("Failed to fetch models:", e.response?.data || e);
        if (!silent) {
          message.error(e.response?.data?.error || "Failed to refresh models");
        }
      } finally {
        setModelsLoading(false);
      }
    },
    [courseId, form]
  );

  const loadCourseAiInfo = useCallback(async () => {
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
      setApiKey("");

      form.setFieldsValue({
        provider: defaultProvider,
        model_name: defaultModel,
        feedback_style: course.default_feedback_style || "balanced",
        temperature: course.default_ai_temperature ?? 0.5,
      });

      if (getKeyStatus(course, defaultProvider)) {
        await fetchModelsForProvider({
          targetProvider: defaultProvider,
          keyOverride: "",
          currentModel: defaultModel,
          silent: true,
        });
      }
    } catch (e) {
      console.error("Failed to load course AI settings:", e);
      message.error("Failed to load AI settings");
    }
  }, [courseId, fetchModelsForProvider, form]);

  useEffect(() => {
    loadCourseAiInfo();
  }, [loadCourseAiInfo]);

  const handleProviderChange = async (newProvider) => {
    setProvider(newProvider);
    setModels([]);
    setApiTestStatus(null);
    setApiKey("");

    const fallbackModel = PROVIDER_DEFAULT_MODELS[newProvider] || "";
    let nextModel = fallbackModel;

    if (newProvider === courseAiInfo.default_ai_provider) {
      const savedModel = courseAiInfo.default_ai_model || fallbackModel;
      nextModel = savedModel;
    }

    setModelName(nextModel);

    form.setFieldsValue({
      provider: newProvider,
      model_name: nextModel,
    });

    if (getKeyStatus(courseAiInfo, newProvider)) {
      await fetchModelsForProvider({
        targetProvider: newProvider,
        keyOverride: "",
        currentModel: nextModel,
        silent: true,
      });
    }
  };

  const handleFetchModels = async () => {
    await fetchModelsForProvider({
      targetProvider: provider,
      keyOverride: apiKey,
      currentModel: modelName,
    });
  };

  const testConnection = async () => {
    try {
      setIsTesting(true);
      setApiTestStatus(null);

      const values = form.getFieldsValue();
      const selectedModel = values.model_name || modelName;

      if (!selectedModel) {
        message.error("Please refresh models and select a model before testing");
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
          "Selected model cannot be used. Please refresh models and choose another model."
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

            <Space wrap>
              <Tag
                color={hasSavedKey ? "success" : "warning"}
                icon={
                  hasSavedKey ? <CheckCircleOutlined /> : <CloseCircleOutlined />
                }
              >
                {isOllama ? "Ollama URL: " : "API key: "}
                {hasSavedKey
                  ? "Connected"
                  : isOllama
                  ? "Using Default"
                  : "Not saved"}
              </Tag>

              <Tag
                color={
                  apiTestStatus === "success"
                    ? "success"
                    : apiTestStatus === "error"
                    ? "error"
                    : "default"
                }
                icon={
                  apiTestStatus === "success" ? (
                    <CheckCircleOutlined />
                  ) : apiTestStatus === "error" ? (
                    <CloseCircleOutlined />
                  ) : null
                }
              >
                Selected model:{" "}
                {apiTestStatus === "success"
                  ? "Tested successfully"
                  : apiTestStatus === "error"
                  ? "Test failed"
                  : "Not tested"}
              </Tag>
            </Space>

            <Card
              title={
                <Space>
                  <KeyOutlined />
                  <span>
                    {isOllama ? "Ollama Server URL" : "Provider API Key"}
                  </span>
                </Space>
              }
            >
              <Space direction="vertical" style={{ width: "100%" }}>
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

                <Alert
                  type={hasSavedKey ? "success" : "info"}
                  showIcon
                  message={
                    hasSavedKey
                      ? isOllama
                        ? "Ollama connection URL is configured"
                        : `${selectedProvider?.label} API key is saved`
                      : isOllama
                      ? "Ollama URL is not configured (defaults to http://host.docker.internal:11434)"
                      : `${selectedProvider?.label} API key is not configured`
                  }
                  description={
                    hasSavedKey
                      ? isOllama
                        ? "A connection URL is configured. Enter a new URL only if you want to replace it."
                        : "A saved key exists. Paste a new key only if you want to replace it."
                      : isOllama
                      ? "Provide the URL to your local or remote Ollama server instance."
                      : "Paste an API key below and save it for this provider."
                  }
                />

                <Form.Item
                  label={isOllama ? "Ollama Base URL" : "Add or Replace API Key"}
                >
                  {isOllama ? (
                    <Input
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="e.g. http://host.docker.internal:11434"
                    />
                  ) : (
                    <Input.Password
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Paste a new API key to add or replace"
                      visibilityToggle
                    />
                  )}
                </Form.Item>

                <Space wrap>
                  <Button type="primary" onClick={handleSave}>
                    Save API Key / Settings
                  </Button>

                  <Button onClick={testConnection} disabled={isTesting}>
                    Test Selected Model
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
                      <CheckCircleOutlined /> Selected model tested successfully
                    </Typography.Text>
                  )}

                  {apiTestStatus === "error" && (
                    <Typography.Text type="danger">
                      <CloseCircleOutlined /> Selected model test failed
                    </Typography.Text>
                  )}
                </Space>
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
                message="Save API key before refreshing models"
                description="Enter or save the provider API key first, then use Refresh Models to load the current usable models for this provider."
              />

              <Form.Item
                label="Default Model"
                name="model_name"
                rules={[
                  {
                    required: true,
                    message: "Please refresh models and select a usable model",
                  },
                ]}
              >
                <Space.Compact style={{ width: "100%" }}>
                  <Button
                    onClick={handleFetchModels}
                    loading={modelsLoading}
                    style={{ width: 180 }}
                  >
                    Refresh Models
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