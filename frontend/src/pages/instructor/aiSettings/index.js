import { CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined } from "@ant-design/icons";

import {
  Button,
  Card,
  Layout,
  Menu,
  Form,
  Input,
  PageHeader,
  Space,
  Typography,
  message,
  Spin
} from "antd";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getCourseInfo, updateCourse } from "../../../services/course";
import axios from "axios";

export default () => {
  const { courseId } = useParams();
  const [form] = Form.useForm();

  // Sidebar models list
  const models = [
    { key: "openai-o-5", provider: "openai", label: "OpenAI o-5" },
    { key: "openai-gpt-4o", provider: "openai", label: "OpenAI GPT-4o" },
    { key: "google-gemini-1.5-pro", provider: "google", label: "Gemini 1.5 Pro" },
    { key: "anthropic-claude-3.5-sonnet", provider: "anthropic", label: "Claude 3.5 Sonnet" },
  ];

  const [selectedModelKey, setSelectedModelKey] = useState(models[0].key);
  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [temperature, setTemperature] = useState(1.0);
  const [isTesting, setIsTesting] = useState(false);
  const [apiTestStatus, setApiTestStatus] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await getCourseInfo({ course_id: courseId });
        const course = res?.data?.[0] || {};
        form.setFieldsValue(course);
        // initialize selected model and provider
        const savedSelected = localStorage.getItem(`ai_selected_model_${courseId}`);
        const modelKey = savedSelected || models[0].key;
        setSelectedModelKey(modelKey);
        const modelMeta = models.find(m => m.key === modelKey) || models[0];
        setProvider(modelMeta.provider);

        // preload OpenAI key from backend column if provider is openai
        const backendOpenAiKey = course.openai_api_key || "";
        const storedProviderKey = localStorage.getItem(`ai_key_${modelMeta.provider}_${courseId}`) || "";
        setApiKey(modelMeta.provider === "openai" ? (backendOpenAiKey || storedProviderKey) : storedProviderKey);

        // per-model temperature
        const savedTempForModel = localStorage.getItem(`ai_temperature_${modelKey}_${courseId}`);
        if (savedTempForModel) setTemperature(parseFloat(savedTempForModel));
      } catch (e) {
        console.error(e);
      }
    };
    load();
  }, [courseId, form]);

  const handleSave = async () => {
    try {
      // persist current selection and per-model temperature
      localStorage.setItem(`ai_selected_model_${courseId}`, selectedModelKey);
      localStorage.setItem(`ai_temperature_${selectedModelKey}_${courseId}`, String(temperature));

      if (provider === "openai") {
        await updateCourse({ course_id: courseId, openai_api_key: apiKey });
        // also mirror into local storage for consistency
        localStorage.setItem(`ai_key_${provider}_${courseId}`, apiKey);
      } else {
        // temporarily cache non-openai keys in localStorage
        localStorage.setItem(`ai_key_${provider}_${courseId}`, apiKey);
      }
      message.success("AI settings saved");
    } catch (e) {
      console.error(e);
      message.error("Failed to save AI settings");
    }
  };

  const testConnection = async () => {
    setIsTesting(true);
    setApiTestStatus(null);
    try {
      if (!apiKey) {
        message.error("Enter API key first");
        setApiTestStatus("error");
        return;
      }
      let ok = false;
      if (provider === "openai") {
        const response = await axios.get("https://api.openai.com/v1/models", {
          headers: { Authorization: `Bearer ${apiKey}` },
        });
        ok = response.status === 200;
      } else if (provider === "google") {
        // Gemini models listing
        const response = await axios.get(
          "https://generativelanguage.googleapis.com/v1beta/models",
          { params: { key: apiKey } }
        );
        ok = response.status === 200;
      } else if (provider === "anthropic") {
        // Claude models listing (simple ping via models is not public; do a harmless messages call with empty content)
        const response = await axios.post(
          "https://api.anthropic.com/v1/messages",
          { model: "claude-3-5-sonnet", max_tokens: 1, messages: [{ role: "user", content: "ping" }] },
          { headers: { "x-api-key": apiKey, "anthropic-version": "2023-06-01", "content-type": "application/json" } }
        );
        ok = response.status >= 200 && response.status < 300;
      }
      if (ok) {
        setApiTestStatus("success");
        message.success("Connected successfully!");
      } else {
        setApiTestStatus("error");
        message.error("Connection failed. Check your key.");
      }
    } catch (e) {
      setApiTestStatus("error");
      message.error("Connection failed. Check your key.");
    } finally {
      setIsTesting(false);
    }
  };

  const handleSelectModel = async (e) => {
    const newKey = e.key;
    setSelectedModelKey(newKey);
    const meta = models.find(m => m.key === newKey) || models[0];
    setProvider(meta.provider);
    // load key for provider; prefer backend for openai if present
    try {
      if (meta.provider === "openai") {
        const res = await getCourseInfo({ course_id: courseId });
        const course = res?.data?.[0] || {};
        const backendOpenAiKey = course.openai_api_key || "";
        const storedProviderKey = localStorage.getItem(`ai_key_${meta.provider}_${courseId}`) || "";
        setApiKey(backendOpenAiKey || storedProviderKey);
      } else {
        const storedProviderKey = localStorage.getItem(`ai_key_${meta.provider}_${courseId}`) || "";
        setApiKey(storedProviderKey);
      }
    } catch (e) {
      console.error(e);
    }
    const savedTempForModel = localStorage.getItem(`ai_temperature_${newKey}_${courseId}`);
    setTemperature(savedTempForModel ? parseFloat(savedTempForModel) : 1.0);
  };

  const { Sider, Content } = Layout;

  return (
    <Layout style={{ background: '#fff', height: '100%', minHeight: '100%' }}>
      <Sider width={260} style={{ background: '#fff', borderRight: '1px solid #f0f2f5' }}>
        <div style={{ padding: '16px' }}>
          <Typography.Title level={4} style={{ margin: 0 }}>AI Models</Typography.Title>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedModelKey]}
          onClick={handleSelectModel}
          items={models.map(m => ({ key: m.key, label: m.label }))}
        />
      </Sider>
      <Content style={{ padding: '0 24px' }}>
        <Form form={form} layout="vertical" style={{ marginLeft: "0px", paddingBottom: '24px' }}>
          <Space direction="vertical" style={{ width: "100%" }}>
            <PageHeader title="AI Settings" subTitle={models.find(m => m.key === selectedModelKey)?.label} />
            <Card title="Credentials">
              <Form.Item label="API Key">
                <Input.Password value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="Enter API key" />
              </Form.Item>
            </Card>
            <Card title="Parameters">
              <Form.Item label="Temperature">
                <Input
                  type="number"
                  min={0}
                  max={2}
                  step={0.1}
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value || 0))}
                  style={{ width: 120 }}
                />
              </Form.Item>
            </Card>
            <Card title="Connection Test">
              <Space>
                <Button type="primary" onClick={testConnection} disabled={isTesting}>Test Connection</Button>
                {isTesting && <Spin indicator={<LoadingOutlined style={{ fontSize: 16 }} spin />} />}
                {apiTestStatus === "success" && (
                  <Typography.Text type="success">
                    <CheckCircleOutlined style={{ marginLeft: 10 }} /> Connected successfully!
                  </Typography.Text>
                )}
                {apiTestStatus === "error" && (
                  <Typography.Text type="danger">
                    <CloseCircleOutlined style={{ marginLeft: 10 }} /> Connection failed. Check your key.
                  </Typography.Text>
                )}
              </Space>
            </Card>
            <Space>
              <Button type="primary" onClick={handleSave}>Save Settings</Button>
            </Space>
          </Space>
        </Form>
      </Content>
    </Layout>
  );
};


