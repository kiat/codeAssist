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

  // Sidebar providers list
  const providers = [
    { key: "openai", label: "ChatGPT" },
    { key: "google", label: "Gemini" },
    { key: "anthropic", label: "Claude" },
  ];

  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [modelName, setModelName] = useState("");
  const [isTesting, setIsTesting] = useState(false);
  const [apiTestStatus, setApiTestStatus] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await getCourseInfo({ course_id: courseId });
        const course = res?.data?.[0] || {};
        form.setFieldsValue(course);
        // initialize selected provider
        const savedProvider = localStorage.getItem(`ai_selected_provider_${courseId}`) || "openai";
        setProvider(savedProvider);

        // preload OpenAI key from backend column if provider is openai
        const backendOpenAiKey = course.openai_api_key || "";
        const storedProviderKey = localStorage.getItem(`ai_key_${savedProvider}_${courseId}`) || "";
        setApiKey(savedProvider === "openai" ? (backendOpenAiKey || storedProviderKey) : storedProviderKey);

        // per-provider model name
        const savedModelName = localStorage.getItem(`ai_model_name_${savedProvider}_${courseId}`) || "";
        setModelName(savedModelName);
      } catch (e) {
        console.error(e);
      }
    };
    load();
  }, [courseId, form]);

  const handleSave = async () => {
    try {
      // persist current selection and per-provider settings
      localStorage.setItem(`ai_selected_provider_${courseId}`, provider);
      localStorage.setItem(`ai_model_name_${provider}_${courseId}`, modelName);

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
    const newProvider = e.key;
    setProvider(newProvider);
    // load key for provider; prefer backend for openai if present
    try {
      if (newProvider === "openai") {
        const res = await getCourseInfo({ course_id: courseId });
        const course = res?.data?.[0] || {};
        const backendOpenAiKey = course.openai_api_key || "";
        const storedProviderKey = localStorage.getItem(`ai_key_${newProvider}_${courseId}`) || "";
        setApiKey(backendOpenAiKey || storedProviderKey);
      } else {
        const storedProviderKey = localStorage.getItem(`ai_key_${newProvider}_${courseId}`) || "";
        setApiKey(storedProviderKey);
      }
    } catch (e) {
      console.error(e);
    }
    const savedModelName = localStorage.getItem(`ai_model_name_${newProvider}_${courseId}`) || "";
    setModelName(savedModelName);
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
          selectedKeys={[provider]}
          onClick={handleSelectModel}
          items={providers.map(p => ({ key: p.key, label: p.label }))}
        />
      </Sider>
      <Content style={{ padding: '0 24px' }}>
        <Form form={form} layout="vertical" style={{ marginLeft: "0px", paddingBottom: '24px' }}>
          <Space direction="vertical" style={{ width: "100%" }}>
            <PageHeader title="AI Settings" subTitle={providers.find(p => p.key === provider)?.label} />
            <Card title="Credentials">
              <Form.Item label="API Key">
                <Input.Password value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="Enter API key" />
              </Form.Item>
            </Card>
            <Card title="Model">
              <Form.Item label="Model Name (e.g., gpt-5o, gemini-1.5-pro, claude-3-5-sonnet)">
                <Input value={modelName} onChange={(e) => setModelName(e.target.value)} placeholder="Enter model name" />
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
            <div style={{ width: '100%', display: 'flex', justifyContent: 'flex-end' }}>
              <Button type="primary" onClick={handleSave}>Save Settings</Button>
            </div>
          </Space>
        </Form>
      </Content>
    </Layout>
  );
};


