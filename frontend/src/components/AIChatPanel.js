import React, { useState, useRef, useEffect, useImperativeHandle, forwardRef } from "react";
import { Button, Spin, Empty } from "antd";
import { RobotOutlined, BulbOutlined, BugOutlined, CodeOutlined, LineChartOutlined, TrophyOutlined } from "@ant-design/icons";

/**
 * DEFAULT_PROMPTS — predefined prompts students can select.
 * Students can ONLY use these prompts; free-text input is disabled.
 */
const DEFAULT_PROMPTS = [
  {
    key: "explain",
    label: "Explain my code",
    icon: <BulbOutlined />,
    message: "Please explain what my code does step by step.",
  },
  {
    key: "debug",
    label: "Help me debug",
    icon: <BugOutlined />,
    message: "I'm having a bug. Can you help me find the issue without giving away the full solution?",
  },
  {
    key: "improve",
    label: "Suggest improvements",
    icon: <CodeOutlined />,
    message: "Can you suggest improvements to my code for efficiency, readability, and style?",
  },
  {
    key: "test",
    label: "Walk me through test cases",
    icon: <LineChartOutlined />,
    message: "Can you walk me through how I might approach testing my code?",
  },
  {
    key: "hint",
    label: "Give me a hint",
    icon: <TrophyOutlined />,
    message: "I'm stuck. Can you give me a hint on how to approach this problem without revealing the solution?",
  },
];

/**
 * AIChatPanel — a preset-prompt chat interface for students to get AI help.
 * Students can ONLY select from default prompts; no free-text input.
 *
 * Props:
 *   onSendMessage  – async (message, code) => string  (returns AI reply)
 *   code           – current code content (sent as context)
 *   disabled       – boolean
 */
const AIChatPanel = forwardRef(function AIChatPanel({ onSendMessage, code = "", disabled = false }, ref) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm your AI coding assistant. Select a prompt below to get help with your code — I can help with debugging, understanding concepts, or suggesting improvements without giving away the full solution.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handlePromptClick = async (prompt) => {
    if (loading || disabled) return;

    const userMsg = { role: "user", content: prompt.label };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const reply = await onSendMessage(prompt.message, code);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (err) {
      const errorMsg = err?.response?.data?.message || err?.message || "Sorry, I encountered an error. Please try again.";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: errorMsg },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Use refs to avoid stale closures in useImperativeHandle
  const onSendMessageRef = useRef(onSendMessage);
  onSendMessageRef.current = onSendMessage;
  const codeRef = useRef(code);
  codeRef.current = code;
  const disabledRef = useRef(disabled);
  disabledRef.current = disabled;

  // Expose sendMessage via ref so parent can trigger feedback requests
  useImperativeHandle(ref, () => ({
    sendMessage: (text) => {
      if (disabledRef.current) return;
      // Map the text to the closest default prompt or use "hint" as fallback
      const matchedPrompt = DEFAULT_PROMPTS.find(
        (p) => p.message === text
      ) || {
        key: "custom",
        label: text,
        message: text,
      };
      setMessages((prev) => [...prev, { role: "user", content: matchedPrompt.label }]);
      setLoading(true);
      onSendMessageRef.current(matchedPrompt.message, codeRef.current)
        .then((reply) => {
          setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
        })
        .catch((err) => {
          const errorMsg = err?.response?.data?.message || err?.message || "Sorry, I encountered an error. Please try again.";
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: errorMsg },
          ]);
        })
        .finally(() => {
          setLoading(false);
        });
    },
  }), []);

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <RobotOutlined style={{ fontSize: 16, color: "#1890ff" }} />
        <span style={styles.headerTitle}>AI Assistant</span>
      </div>

      {/* Messages */}
      <div style={styles.messagesContainer}>
        {messages.length === 1 && !loading && (
          <div style={styles.emptyState}>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="Select a prompt to get started!"
              style={{ marginTop: 40 }}
            />
          </div>
        )}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              ...styles.messageRow,
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
            }}
          >
            {msg.role === "assistant" && (
              <div style={styles.avatar}>
                <RobotOutlined style={{ fontSize: 14, color: "#1890ff" }} />
              </div>
            )}
            <div
              style={{
                ...styles.bubble,
                backgroundColor: msg.role === "user" ? "#1890ff" : "#f0f0f0",
                color: msg.role === "user" ? "#fff" : "#333",
                borderRadius:
                  msg.role === "user"
                    ? "12px 12px 4px 12px"
                    : "12px 12px 12px 4px",
              }}
            >
              <div style={styles.messageContent}>{msg.content}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ ...styles.messageRow, justifyContent: "flex-start" }}>
            <div style={styles.avatar}>
              <RobotOutlined style={{ fontSize: 14, color: "#1890ff" }} />
            </div>
            <div style={{ ...styles.bubble, backgroundColor: "#f0f0f0" }}>
              <Spin size="small" />
              <span style={{ marginLeft: 8, color: "#999", fontSize: 12 }}>
                Thinking...
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Preset Prompt Buttons */}
      <div style={styles.promptArea}>
        <div style={styles.promptLabel}>Select a prompt:</div>
        <div style={styles.promptGrid}>
          {DEFAULT_PROMPTS.map((prompt) => (
            <Button
              key={prompt.key}
              size="small"
              icon={prompt.icon}
              onClick={() => handlePromptClick(prompt)}
              disabled={loading || disabled}
              style={styles.promptButton}
            >
              {prompt.label}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
});

export default AIChatPanel;

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    border: "1px solid #d9d9d9",
    borderRadius: 6,
    overflow: "hidden",
    backgroundColor: "#fff",
    height: "100%",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "10px 14px",
    borderBottom: "1px solid #f0f0f0",
    backgroundColor: "#fafafa",
    flexShrink: 0,
  },
  headerTitle: {
    fontWeight: 600,
    fontSize: 14,
    color: "#333",
  },
  messagesContainer: {
    flex: 1,
    overflowY: "auto",
    padding: "12px 10px",
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  emptyState: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    flex: 1,
  },
  messageRow: {
    display: "flex",
    alignItems: "flex-end",
    gap: 6,
  },
  avatar: {
    width: 28,
    height: 28,
    borderRadius: "50%",
    backgroundColor: "#e6f7ff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  bubble: {
    maxWidth: "80%",
    padding: "8px 12px",
    fontSize: 13,
    lineHeight: "1.5",
    wordBreak: "break-word",
  },
  messageContent: {
    whiteSpace: "pre-wrap",
  },
  promptArea: {
    padding: "8px 10px",
    borderTop: "1px solid #f0f0f0",
    backgroundColor: "#fafafa",
    flexShrink: 0,
  },
  promptLabel: {
    fontSize: 11,
    color: "#999",
    marginBottom: 6,
  },
  promptGrid: {
    display: "flex",
    flexWrap: "wrap",
    gap: 4,
  },
  promptButton: {
    fontSize: 11,
    height: 28,
    borderRadius: 14,
  },
};
