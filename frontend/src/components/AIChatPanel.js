import React, { useState, useRef, useEffect, useImperativeHandle, forwardRef } from "react";
import { Button, Input, Spin, Empty } from "antd";
import { SendOutlined, RobotOutlined, UserOutlined } from "@ant-design/icons";

/**
 * AIChatPanel — a chat interface for students to converse with an AI agent
 * about their current code.
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
        "Hi! I'm your AI coding assistant. Ask me anything about your code — I can help with debugging, understanding concepts, or suggesting improvements without giving away the full solution.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading || disabled) return;

    // Add user message
    const userMsg = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const reply = await onSendMessage(trimmed, code);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (err) {
      const errorMsg = err?.response?.data?.message || err?.message || "Sorry, I encountered an error. Please try again.";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: errorMsg,
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
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
      const trimmed = text.trim();
      if (!trimmed || disabledRef.current) return;
      setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
      setLoading(true);
      onSendMessageRef.current(trimmed, codeRef.current)
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

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

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
              description="Ask me about your code!"
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
            {msg.role === "user" && (
              <div style={styles.avatar}>
                <UserOutlined style={{ fontSize: 14, color: "#666" }} />
              </div>
            )}
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

      {/* Input */}
      <div style={styles.inputArea}>
        <Input.TextArea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your code..."
          autoSize={{ minRows: 1, maxRows: 3 }}
          disabled={disabled || loading}
          style={styles.input}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          disabled={!input.trim() || loading || disabled}
          style={{ marginLeft: 8, flexShrink: 0 }}
        />
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
  inputArea: {
    display: "flex",
    alignItems: "flex-end",
    padding: "8px 10px",
    borderTop: "1px solid #f0f0f0",
    backgroundColor: "#fafafa",
    flexShrink: 0,
  },
  input: {
    flex: 1,
    borderRadius: 6,
  },
};
