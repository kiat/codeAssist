import React, { useState, useEffect, useCallback, useRef, useContext } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { PageHeader, message, Spin, Button, Modal } from "antd";
import { GlobalContext } from "../../App";
import CodeEditor from "../../components/CodeEditor";
import AIChatPanel from "../../components/AIChatPanel";
import VersionHistoryModal from "../../components/VersionHistoryModal";
import { getAssignment, getExtension } from "../../services/assignment";
import { aiChat, saveCodeDraft, getLatestDraft, submitCode, runCode } from "../../services/submission";
import moment from "moment";

/**
 * CodeEditorPage — the main page for inline code editing.
 * Left panel: CodeEditor with line numbers, auto-save, submit, feedback.
 * Right panel: AIChatPanel for conversing with the AI agent.
 *
 * Route: /codeEditor/:assignmentId
 */
export default function CodeEditorPage() {
  const { assignmentId } = useParams();
  const navigate = useNavigate();
  const { userInfo, courseInfo } = useContext(GlobalContext);

  // Code state
  const [code, setCode] = useState("# Write your solution here\n");
  const [fileName, setFileName] = useState("solution.py");
  const [assignmentName, setAssignmentName] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Auto-save state
  const [autoSaveStatus, setAutoSaveStatus] = useState("idle");
  const autoSaveTimerRef = useRef(null);
  const lastSavedCodeRef = useRef(null);
  const draftIdRef = useRef(null);

  // Version history
  const [historyOpen, setHistoryOpen] = useState(false);

  // Due date checks
  const [dueDate, setDueDate] = useState(null);
  const [lateDueDate, setLateDueDate] = useState(null);
  const [lateAllowed, setLateAllowed] = useState(false);

  // Run code output state
  const [runOutput, setRunOutput] = useState(null);

  // AI chat callback — uses the service helper which hits URL_PREFIX (localhost:5001)
  const handleAiChat = useCallback(
    async (message, currentCode) => {
      try {
        const res = await aiChat({
          student_id: userInfo.id,
          assignment_id: assignmentId,
          message,
          code: currentCode,
        });
        return res.data.reply;
      } catch (err) {
        // Return the error as a normal reply so the chat panel shows it
        // without the axios interceptor toast doubling up
        return err?.response?.data?.message || err?.message || "Sorry, I encountered an error. Please try again.";
      }
    },
    [userInfo.id, assignmentId]
  );

  // Fetch assignment details and latest draft on mount
  useEffect(() => {
    const init = async () => {
      if (!userInfo?.id || !assignmentId) return;
      setLoading(true);
      try {
        // Fetch assignment info
        const [assignRes, extRes] = await Promise.all([
          getAssignment({ assignment_id: assignmentId }),
          getExtension({ assignment_id: assignmentId, student_id: userInfo.id }),
        ]);

        if (assignRes?.data) {
          setAssignmentName(assignRes.data.name);
          const nameLower = assignRes.data.name?.toLowerCase().replace(/\s+/g, "_");
          setFileName(nameLower ? `${nameLower}.py` : "solution.py");

          if (assignRes.data.due_date) {
            setDueDate(moment(assignRes.data.due_date).valueOf());
          }
          setLateAllowed(assignRes.data.late_submission);
          if (assignRes.data.late_due_date) {
            setLateDueDate(moment(assignRes.data.late_due_date).valueOf());
          }
          if (extRes?.data?.due_date_extension) {
            setDueDate(moment(extRes.data.due_date_extension).valueOf());
          }
          if (extRes?.data?.late_due_date_extension) {
            setLateDueDate(moment(extRes.data.late_due_date_extension).valueOf());
            setLateAllowed(true);
          }
        }

        // Fetch latest draft
        const draftRes = await getLatestDraft({
          student_id: userInfo.id,
          assignment_id: assignmentId,
        });
        if (draftRes?.data && draftRes.data.content) {
          setCode(draftRes.data.content);
          draftIdRef.current = draftRes.data.id;
          lastSavedCodeRef.current = draftRes.data.content;
        }
      } catch (err) {
        console.error("Failed to load assignment:", err);
        message.error("Failed to load assignment details");
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [assignmentId, userInfo?.id]);

  // Save draft (auto or manual)
  const saveDraft = useCallback(
    async (isAuto = false) => {
      if (!userInfo?.id || !assignmentId) return;
      if (code === lastSavedCodeRef.current && isAuto) return;

      setAutoSaveStatus("saving");
      try {
        const currentFileName = fileNameRef.current;
        const res = await saveCodeDraft({
          student_id: userInfo.id,
          assignment_id: assignmentId,
          content: code,
          file_name: currentFileName,
          auto_saved: isAuto,
        });

        draftIdRef.current = res.data.id;
        lastSavedCodeRef.current = code;
        setAutoSaveStatus("saved");

        // Reset to idle after 3 seconds
        setTimeout(() => setAutoSaveStatus("idle"), 3000);
      } catch (err) {
        console.error("Save draft error:", err);
        setAutoSaveStatus("error");
      }
    },
    [code, userInfo?.id, assignmentId]
  );

  // Ref to hold latest saveDraft for use in intervals/handlers
  const saveDraftRef = useRef(saveDraft);
  saveDraftRef.current = saveDraft;

  // Auto-save: save every 30 seconds if code has changed
  const codeRef = useRef(code);
  codeRef.current = code;
  const fileNameRef = useRef(fileName);
  fileNameRef.current = fileName;
  const autoSaveStatusRef = useRef(autoSaveStatus);
  autoSaveStatusRef.current = autoSaveStatus;

  useEffect(() => {
    autoSaveTimerRef.current = setInterval(() => {
      if (
        codeRef.current &&
        codeRef.current !== lastSavedCodeRef.current &&
        autoSaveStatusRef.current !== "saving"
      ) {
        saveDraftRef.current(true);
      }
    }, 30000);

    return () => clearInterval(autoSaveTimerRef.current);
  }, []);

  // Check due date before action
  const checkDueDate = useCallback(() => {
    const now = moment();
    if (dueDate && now.isAfter(dueDate)) {
      if (lateAllowed && lateDueDate && now.isBefore(lateDueDate)) {
        return true; // In late period
      }
      return false; // Past due
    }
    return true; // Before due
  }, [dueDate, lateDueDate, lateAllowed]);

  const [running, setRunning] = useState(false);

  const handleRun = useCallback(async () => {
    if (!code.trim()) {
      message.error("Cannot run empty code");
      return;
    }
    setRunOutput(null);
    setRunning(true);
    try {
      const res = await runCode({
        student_id: userInfo.id,
        assignment_id: assignmentId,
        content: code,
        file_name: fileName,
      });
      setRunOutput(res.data);
      if (res.data.passed) {
        message.success("Code ran successfully!");
      } else {
        message.warning("Code finished with issues. Check output below.");
      }
    } catch (err) {
      console.error("Run error:", err);
      message.error(err.message || "Failed to run code");
      setRunOutput({ output: err.message || "Run failed", passed: false, tests: [] });
    } finally {
      setRunning(false);
    }
  }, [code, userInfo?.id, assignmentId, fileName]);

  // Submit code for grading
  const handleSubmit = useCallback(async () => {
    if (!code.trim()) {
      message.error("Cannot submit empty code");
      return;
    }
    if (!checkDueDate()) {
      message.error("Due date has passed");
      return;
    }

    // Confirm submission
    Modal.confirm({
      title: "Submit Code",
      content: "Are you sure you want to submit your code for grading?",
      okText: "Submit",
      cancelText: "Cancel",
      onOk: async () => {
        setSubmitting(true);
        try {
          const res = await submitCode({
            student_id: userInfo.id,
            assignment_id: assignmentId,
            content: code,
            file_name: fileName,
          });

          message.success("Code submitted successfully!");
          navigate(`/assignmentResult/${res.data.submissionID}`);
        } catch (err) {
          console.error("Submit error:", err);
          message.error(err.message || "Failed to submit code");
        } finally {
          setSubmitting(false);
        }
      },
    });
  }, [code, userInfo?.id, assignmentId, fileName, checkDueDate, navigate]);

  // Request feedback — sends the code to the AI chat panel for review
  const chatPanelRef = useRef(null);

  const handleRequestFeedback = useCallback(async () => {
    if (!code.trim()) {
      message.error("Cannot request feedback on empty code");
      return;
    }
    message.info("Requesting AI feedback...");
    // Trigger a feedback request through the AI chat by simulating a message
    if (chatPanelRef.current) {
      chatPanelRef.current.sendMessage("Please review my code and provide feedback on correctness, style, and potential improvements.");
    }
  }, [code]);

  // Handle selecting a version from history
  const handleSelectVersion = useCallback((content) => {
    setCode(content);
    message.success("Version restored");
  }, []);

  // Ctrl+S keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        saveDraftRef.current(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%" }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <Button type="link" onClick={() => navigate(-1)} style={{ padding: 0 }}>
            ← Back
          </Button>
          <PageHeader
            title={assignmentName || "Code Editor"}
            subTitle={courseInfo?.name || ""}
            style={{ padding: "0 0 0 12px" }}
          />
        </div>
      </div>

      {/* Main content: Editor + Chat */}
      <div style={styles.content}>
        {/* Left: Code Editor */}
        <div style={styles.editorPanel}>
          <CodeEditor
            value={code}
            onChange={setCode}
            onSave={() => saveDraft(false)}
            onSubmit={handleSubmit}
            onRun={handleRun}
            onRequestFeedback={handleRequestFeedback}
            onOpenHistory={() => setHistoryOpen(true)}
            autoSaveStatus={autoSaveStatus}
            fileName={fileName}
            onFileNameChange={(name) => {
              setFileName(name);
              saveDraftRef.current(false);
            }}
            language="python"
            readOnly={submitting}
          />
          {runOutput && (
            <div style={styles.outputPanel}>
              <div style={styles.outputHeader}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>
                  {runOutput.passed ? (
                    <span style={{ color: '#52c41a' }}>✓ Passed</span>
                  ) : (
                    <span style={{ color: '#ff4d4f' }}>✗ Failed</span>
                  )}
                  {' '}— Output
                </span>
                <Button size="small" type="text" onClick={() => setRunOutput(null)} style={{ color: '#abb2bf' }}>Close</Button>
              </div>
              <pre style={styles.outputContent}>{runOutput.output || "(no output)"}</pre>
              {runOutput.tests && runOutput.tests.length > 0 && (
                <div style={{ borderTop: '1px solid #3e4451', padding: '8px 12px' }}>
                  <div style={{ fontWeight: 600, fontSize: 12, color: '#abb2bf', marginBottom: 6 }}>
                    Test Results ({runOutput.tests.filter(t => t.status === 'passed').length}/{runOutput.tests.length} passed)
                  </div>
                  {runOutput.tests.map((t, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, fontSize: 12 }}>
                      <span style={{ color: t.status === 'passed' ? '#52c41a' : '#ff4d4f' }}>
                        {t.status === 'passed' ? '✓' : '✗'}
                      </span>
                      <span style={{ color: '#abb2bf' }}>{t.name || `Test ${i + 1}`}</span>
                      {t.score !== undefined && (
                        <span style={{ color: '#636d83', marginLeft: 'auto' }}>
                          {t.score}/{t.max_score}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {runOutput.score !== undefined && runOutput.tests && runOutput.tests.length > 0 && (
                <div style={{ borderTop: '1px solid #3e4451', padding: '6px 12px', fontSize: 12, color: '#abb2bf' }}>
                  Score: {runOutput.score}
                </div>
              )}
            </div>
          )}
          {running && (
            <div style={{ ...styles.outputPanel, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
              <Spin size="small" /> <span style={{ color: '#abb2bf', marginLeft: 8, fontSize: 12 }}>Running code…</span>
            </div>
          )}
        </div>

        {/* Right: AI Chat */}
        <div style={styles.chatPanel}>
          <AIChatPanel
            ref={chatPanelRef}
            onSendMessage={handleAiChat}
            code={code}
            disabled={submitting}
          />
        </div>
      </div>

      {/* Version History Modal */}
      <VersionHistoryModal
        open={historyOpen}
        onCancel={() => setHistoryOpen(false)}
        onSelectVersion={handleSelectVersion}
        studentId={userInfo?.id}
        assignmentId={assignmentId}
      />
    </div>
  );
}

const styles = {
  page: {
    display: "flex",
    flexDirection: "column",
    height: "calc(100vh - 40px)",
    overflow: "hidden",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "8px 16px",
    borderBottom: "1px solid #f0f0f0",
    backgroundColor: "#fff",
    flexShrink: 0,
  },
  headerLeft: {
    display: "flex",
    alignItems: "center",
  },
  content: {
    display: "flex",
    flex: 1,
    overflow: "hidden",
    padding: 12,
    gap: 12,
  },
  editorPanel: {
    flex: "1 1 65%",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    minWidth: 0,
  },
  chatPanel: {
    flex: "0 0 35%",
    maxWidth: 420,
    minWidth: 300,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  outputPanel: {
    marginTop: 8,
    border: "1px solid #3e4451",
    borderRadius: 6,
    backgroundColor: "#1e2127",
    overflow: "hidden",
  },
  outputHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "6px 12px",
    borderBottom: "1px solid #3e4451",
    backgroundColor: "#21252b",
    color: "#abb2bf",
  },
  outputContent: {
    margin: 0,
    padding: "10px 12px",
    fontSize: 12,
    fontFamily: "'SFMono-Regular', Consolas, monospace",
    color: "#abb2bf",
    backgroundColor: "#282c34",
    maxHeight: 200,
    overflowY: "auto",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
  },
};
