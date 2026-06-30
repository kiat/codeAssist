import React, { useState, useRef, useEffect, useImperativeHandle, forwardRef, useCallback } from "react";
import { Button, Spin, Empty, Tag, Tooltip } from "antd";
import {
  RobotOutlined,
  BulbOutlined,
  BugOutlined,
  CodeOutlined,
  LineChartOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  LockOutlined,
} from "@ant-design/icons";
import { getAssignmentPrompts } from "../services/assignment";
import { aiFeedbackStatus } from "../services/submission";

/**
 * Icon map for prompt IDs to give each prompt a visual identity.
 */
const PROMPT_ICONS = {
  check_correctness: <BulbOutlined />,
  debug_failed_tests: <BugOutlined />,
  review_edge_cases: <LineChartOutlined />,
  explain_runtime_errors: <BulbOutlined />,
  review_code_style: <CodeOutlined />,
  suggest_algorithmic_improvements: <TrophyOutlined />,
};

function getPromptIcon(promptId) {
  return PROMPT_ICONS[promptId] || <BulbOutlined />;
}

/**
 * AIChatPanel — a preset-prompt chat interface for students to get AI help.
 * Students can ONLY select from instructor-configured prompts; no free-text input.
 *
 * Props:
 *   onSendMessage  – async (message, code, promptId) => { reply, feedback_status }
 *   code           – current code content (sent as context)
 *   disabled       – boolean
 *   assignmentId   – the assignment ID (to fetch prompts and limits)
 *   studentId      – the student ID (to check feedback status)
 */
const AIChatPanel = forwardRef(function AIChatPanel(
  { onSendMessage, code = "", disabled = false, assignmentId, studentId },
  ref
) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm your AI coding assistant. Select a prompt below to get help with your code — I can help with debugging, understanding concepts, or suggesting improvements without giving away the full solution.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Instructor-configured prompts
  const [prompts, setPrompts] = useState([]);
  const [promptsLoading, setPromptsLoading] = useState(true);

  // Feedback status (remaining requests, wait time)
  const [feedbackStatus, setFeedbackStatus] = useState({
    remaining: null,
    wait_seconds: 0,
    max_requests: null,
    total_requests: 0,
  });

  // Countdown timer
  const [countdown, setCountdown] = useState(0);
  const countdownRef = useRef(null);

  // Fetch instructor-configured prompts on mount
  useEffect(() => {
    if (!assignmentId || !studentId) {
      setPromptsLoading(false);
      return;
    }

    const fetchPrompts = async () => {
      try {
        const res = await getAssignmentPrompts(assignmentId);
        const data = res?.data || {};
        // Check if AI feedback is enabled for this assignment
        if (data.ai_feedback_enabled === false) {
          setPrompts([]);
          return;
        }
        // Filter to only enabled prompts (backend should already do this, but defense-in-depth)
        const enabledPrompts = (data.ai_feedback_prompts || []).filter((p) => p.enabled);
        setPrompts(enabledPrompts);
      } catch (err) {
        console.error("Failed to load AI feedback prompts:", err);
        // Fallback to empty — student sees no prompts
        setPrompts([]);
      } finally {
        setPromptsLoading(false);
      }
    };

    fetchPrompts();
  }, [assignmentId, studentId]);

  // Fetch feedback status on mount and after each request
  const fetchStatus = useCallback(async () => {
    if (!assignmentId || !studentId) return;
    try {
      const res = await aiFeedbackStatus({
        student_id: studentId,
        assignment_id: assignmentId,
      });
      setFeedbackStatus(res?.data || {});

      // Start countdown if there's wait time
      const waitSec = res?.data?.wait_seconds || 0;
      if (waitSec > 0) {
        setCountdown(waitSec);
      }
    } catch (err) {
      console.error("Failed to fetch feedback status:", err);
    }
  }, [assignmentId, studentId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Countdown timer
  useEffect(() => {
    if (countdown > 0) {
      countdownRef.current = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(countdownRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
      }
    };
  }, [countdown > 0]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Determine if prompts should be disabled
  const isDisabled =
    disabled ||
    loading ||
    (feedbackStatus.max_requests !== null && feedbackStatus.remaining === 0) ||
    countdown > 0;

  const handlePromptClick = async (prompt) => {
    if (isDisabled) return;

    // Send the prompt title as the user message, NOT the full prompt text.
    // The backend resolves the full prompt via prompt_id and prepends it only
    // for the OpenAI API call — this avoids inflating chat history with
    // redundant prompt text and prevents the prompt being sent twice.
    const userMsg = { role: "user", content: prompt.title };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const result = await onSendMessage(prompt.title, code, prompt.id);
      // Handle both old format (string) and new format (object with reply + feedback_status)
      const reply =
        typeof result === "string" ? result : result?.reply || "No response received.";
      const status =
        typeof result === "object" ? result?.feedback_status : null;

      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);

      // Update feedback status from response
      if (status) {
        setFeedbackStatus(status);
        if (status.wait_seconds > 0) {
          setCountdown(status.wait_seconds);
        }
      } else {
        // Fallback: re-fetch status
        fetchStatus();
      }
    } catch (err) {
      const errorMsg =
        err?.response?.data?.message ||
        err?.message ||
        "Sorry, I encountered an error. Please try again.";
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
    sendMessage: (text, promptId) => {
      if (disabledRef.current) return;
      const matchedPrompt = prompts.find((p) => p.id === promptId) || {
        id: "custom",
        title: text,
        prompt: text,
      };
      setMessages((prev) => [...prev, { role: "user", content: matchedPrompt.title }]);
      setLoading(true);
      onSendMessageRef.current(matchedPrompt.prompt, codeRef.current, matchedPrompt.id)
        .then((result) => {
          const reply =
            typeof result === "string" ? result : result?.reply || "No response received.";
          const status =
            typeof result === "object" ? result?.feedback_status : null;
          setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
          if (status) {
            setFeedbackStatus(status);
            if (status.wait_seconds > 0) {
              setCountdown(status.wait_seconds);
            }
          }
        })
        .catch((err) => {
          const errorMsg =
            err?.response?.data?.message ||
            err?.message ||
            "Sorry, I encountered an error. Please try again.";
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: errorMsg },
          ]);
        })
        .finally(() => {
          setLoading(false);
        });
    },
  }));

  // Format countdown as MM:SS
  const formatCountdown = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <RobotOutlined style={{ fontSize: 16, color: "#1890ff" }} />
        <span style={styles.headerTitle}>AI Assistant</span>
        {feedbackStatus.max_requests !== null && (
          <Tooltip title="Remaining feedback requests">
            <Tag
              color={feedbackStatus.remaining === 0 ? "red" : "blue"}
              style={{ marginLeft: "auto", fontSize: 11 }}
            >
              {feedbackStatus.remaining === 0 ? (
                <>
                  <LockOutlined /> Limit reached
                </>
              ) : (
                <>
                  {feedbackStatus.remaining} left
                </>
              )}
            </Tag>
          </Tooltip>
        )}
      </div>

      {/* Countdown banner */}
      {countdown > 0 && (
        <div style={styles.countdownBanner}>
          <ClockCircleOutlined style={{ marginRight: 6 }} />
          Please wait {formatCountdown(countdown)} before requesting feedback again
        </div>
      )}

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
        <div style={styles.promptLabel}>
          {promptsLoading
            ? "Loading prompts..."
            : prompts.length === 0
            ? "No prompts available"
            : "Select a prompt:"}
        </div>
        <div style={styles.promptGrid}>
          {prompts.map((prompt) => (
            <Tooltip key={prompt.id} title={prompt.prompt} placement="top">
              <Button
                size="small"
                icon={getPromptIcon(prompt.id)}
                onClick={() => handlePromptClick(prompt)}
                disabled={isDisabled}
                style={styles.promptButton}
              >
                {prompt.title}
              </Button>
            </Tooltip>
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
  countdownBanner: {
    padding: "6px 14px",
    backgroundColor: "#fff7e6",
    borderBottom: "1px solid #ffd591",
    color: "#d46b08",
    fontSize: 12,
    display: "flex",
    alignItems: "center",
    flexShrink: 0,
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
