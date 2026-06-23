import React, { useContext, useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { GlobalContext } from "../../App";
import { Alert, Collapse, Button, Tooltip, Spin, Tag, Modal } from "antd";
import { useRef } from "react";

import "antd/dist/antd.css";
import StudentInfoPanel from "./StudentInfoPanel";

const { Panel } = Collapse;

//can also be displayed as a modal
const TestResultsDisplay = ({ viewMode, studentId, assignmentName, studentName, score, totalPoints, assignmentId, data, aiFeedbackEnabled, isModal = false, submissionId: submissionIdFromProps, onCancel }) => {
  const { userInfo } = useContext(GlobalContext);
  const params = useParams();
  const submissionId = submissionIdFromProps || params.submissionId; //const { assignmentId } = useParams();
  const navigate = useNavigate();
  const [testResults, setTestResults] = useState(null);
  const [studentCode, setStudentCode] = useState("");
  const [studentFileName, setStudentFileName] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [StudScore, setStudScore] = useState(score);

  const [highlightedLines, setHighlightedLines] = useState([]);
  const [annotations, setAnnotations] = useState([]);
  const [aiFeedback, setAiFeedback] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState("null"); // 'loading', 'success', 'error', or null

  // used to store the line references for scrolling to
  const lineRefs = useRef({});

  useEffect(() => {
    if (!userInfo || !userInfo.id) {
      navigate("/");
      return;
    }
    if (!submissionId) {
      console.error("No submission_id provided");
      return;
    }
    setIsLoading(true);
    if (data) {
      setStudScore(data?.score ?? "UNGRADED");
      const parsedResults = typeof data?.results === "string" ? JSON.parse(data.results) : data?.results || { tests: [] };
      setTestResults(parsedResults);
      setStudentCode(data.student_code_file);
      setStudentFileName(data.file_name);
    } else {
      console.error("not available");
    }
    setIsLoading(false);
  }, [submissionId, navigate, userInfo, data]);

  const getAiAnnotations = useCallback(() => {
    if (!aiFeedbackEnabled) {
      // setAiFeedbackEnabled(false);
      setLoadingStatus(null);
      return null;
    }

    if (data && data.ai_feedback !== undefined && data.ai_feedback !== null) {
      if (typeof data.ai_feedback === "string") {
        try {
          const parsed = JSON.parse(data.ai_feedback);
          return parsed;
        } catch (error) {
          console.error("Error parsing ai_feedback from JSON:", error);
          setLoadingStatus("error");
          return null;
        }
      }

      if (typeof data.ai_feedback === "object") {
        return data.ai_feedback;
      }

      console.error("AI Feedback has an unsupported format", data.ai_feedback);
      setLoadingStatus("error");
      return null;
    } else {
      // ai_feedback is still being generated or fetched
      console.log("ai_feedback is still being generated or fetched");
      console.log(data, data.ai_feedback);
      setLoadingStatus("loading");
      return null;
    }
  }, [aiFeedbackEnabled, data]);

  const findAnnotations = useCallback((code) => {
    if (!aiFeedbackEnabled) {
      setAiFeedback(null);
      setHighlightedLines([]);
      setAnnotations([]);
      setLoadingStatus(null);
      return;
    }

    setLoadingStatus("loading");

    const aiAnnotations = getAiAnnotations();
    if (!aiAnnotations) {
      setAiFeedback(null);
      setLoadingStatus("loading");
      return;
    }

    if (aiAnnotations.error) {
      console.error("AI feedback error:", aiAnnotations.error);
      setAiFeedback({
        error: aiAnnotations.error,
        insights: Array.isArray(aiAnnotations.insights) ? aiAnnotations.insights : [],
        annotations: [],
      });
      setLoadingStatus("error");
      return;
    }

    const feedbackInsights = Array.isArray(aiAnnotations.insights)
      ? aiAnnotations.insights
      : [];
    const feedbackAnnotations = Array.isArray(aiAnnotations.annotations)
      ? aiAnnotations.annotations
      : [];

    if (
      !Array.isArray(aiAnnotations.insights) &&
      !Array.isArray(aiAnnotations.annotations)
    ) {
      console.error("Missing or invalid AI feedback arrays.");
      setLoadingStatus("error");
      return;
    }

    setAiFeedback({
      ...aiAnnotations,
      insights: feedbackInsights,
      annotations: feedbackAnnotations,
    });

    const lines = code.split("\n");
    const highlighted = [];
    const newAnnotations = [];

    const escapeRegExp = (string) => string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); // $& means the whole match

    feedbackAnnotations.forEach(({ pattern, comment }) => {
      if (!pattern || !comment) {
        return;
      }

      let regex;
      try {
        const safePattern = escapeRegExp(pattern.trim()); // Escape special characters
        regex = new RegExp(safePattern);
      } catch (e) {
        console.warn(`Invalid regex pattern skipped: ${pattern}`, e);
        return;
      }

      lines.forEach((line, index) => {
        if (regex.test(line)) {
          highlighted.push(index + 1);
          newAnnotations.push({ line: index + 1, comment, pattern: pattern });
        }
      });
    });

    setHighlightedLines(highlighted);
    setAnnotations(newAnnotations);
    setLoadingStatus("success");
  }, [aiFeedbackEnabled, getAiAnnotations]);

  useEffect(() => {
    if (data) {
      setStudentCode(data.student_code_file || "");
      // setAiFeedbackEnabled(true);
      findAnnotations(data.student_code_file || "");
    }
  }, [data, findAnnotations]);

  const fetchSubmissionDetails = useCallback(async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/get_submission_details?submission_id=${submissionId}`);
      const data = await response.json();
      setStudScore(data.score ?? "UNGRADED");
    } catch (error) {
      console.error("Failed to fetch updated submission details:", error);
    }
  }, [submissionId]);

  useEffect(() => {
    fetchSubmissionDetails();
  }, [fetchSubmissionDetails]);

  const displayCodeWithAnnotations = () => {
    const lines = studentCode.split("\n");

    return (
      <div style={{ position: "relative", maxHeight: "400px", overflowY: "scroll", border: "1px solid #ccc", padding: "10px" }}>
        {/* Loader/Status only if AI feedback is enabled */}
        {aiFeedbackEnabled && (
          <div style={{ position: "absolute", top: 5, right: 10, display: "flex", alignItems: "center", gap: "8px" }}>
            <Tooltip title="Fetching AI feedback...">{loadingStatus === "loading" && <Spin size="small" />}</Tooltip>

            {loadingStatus === "success" && (
              <Tooltip title="AI feedback was successfully loaded. Summary feedback may appear even when no line annotations are returned.">
                <Tag color="green">AI Feedback Ready</Tag>
              </Tooltip>
            )}

            {loadingStatus === "error" && (
              <Tooltip title="An error occurred while parsing or loading AI feedback.">
                <Tag color="red">AI Feedback Error</Tag>
              </Tooltip>
            )}
          </div>
        )}

        <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
          {lines.map((line, index) => {
            const lineNumber = index + 1;
            const isHighlighted = highlightedLines.includes(lineNumber);
            const annotation = annotations.find((a) => a.line === lineNumber);

            return (
              <Tooltip key={lineNumber} title={annotation ? annotation.comment : ""}>
                <div
                  key={lineNumber}
                  ref={(el) => {
                    if (el) lineRefs.current[lineNumber] = el;
                  }}
                  style={{
                    backgroundColor: isHighlighted ? "#ffe6e6" : "transparent",
                    padding: "2px 0",
                    margin: "2px 0",
                    borderLeft: isHighlighted ? "5px solid red" : "none",
                  }}
                >
                  {line}
                </div>
              </Tooltip>
            );
          })}
        </pre>
        <Button type="primary" style={{ marginTop: "10px" }}>
          Download
        </Button>
      </div>
    );
  };

  const renderAiFeedbackSummary = () => {
    if (!aiFeedbackEnabled) {
      return null;
    }

    if (loadingStatus === "loading") {
      return (
        <Alert
          type="info"
          showIcon
          style={{ marginTop: 20 }}
          message="AI feedback is generating"
          description="Refresh this submission shortly to see feedback after the model finishes."
        />
      );
    }

    if (loadingStatus === "error") {
      return (
        <Alert
          type="error"
          showIcon
          style={{ marginTop: 20 }}
          message="AI feedback unavailable"
          description={
            aiFeedback?.error ||
            "The AI feedback response could not be loaded or parsed."
          }
        />
      );
    }

    if (loadingStatus !== "success" || !aiFeedback) {
      return null;
    }

    const insights = Array.isArray(aiFeedback.insights) ? aiFeedback.insights : [];
    const hasLineAnnotations = annotations.length > 0;

    return (
      <div style={{ marginTop: 20 }}>
        {insights.length > 0 && (
          <Alert
            type="success"
            showIcon
            message="AI Feedback Summary"
            description={
              <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                {insights.map((insight, index) => (
                  <li key={`${insight}-${index}`}>{insight}</li>
                ))}
              </ul>
            }
            style={{ marginBottom: 16 }}
          />
        )}

        {!hasLineAnnotations && (
          <Alert
            type="info"
            showIcon
            message="No line-by-line annotations"
            description="AI feedback was generated successfully, but it did not identify a specific code line that needed a comment."
            style={{ marginBottom: 16 }}
          />
        )}

        {hasLineAnnotations && (
          <div>
            <h3>Line Feedback</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {annotations.map((annotation, index) => (
                <div
                  key={index}
                  onClick={() => {
                    const lineEl = lineRefs.current[annotation.line];
                    if (lineEl) {
                      lineEl.scrollIntoView({ behavior: "smooth", block: "center" });
                      lineEl.style.transition = "background-color 0.5s";
                      lineEl.style.backgroundColor = "#fff7d6";
                      setTimeout(() => {
                        lineEl.style.backgroundColor = "#ffe6e6";
                      }, 1500);
                    }
                  }}
                  style={{
                    cursor: "pointer",
                    backgroundColor: "#fafafa",
                    border: "1px solid #ddd",
                    borderLeft: "5px solid #1890ff",
                    padding: "10px",
                    borderRadius: "4px",
                  }}
                >
                  <div
                    style={{
                      fontWeight: "bold",
                      color: "#333",
                      marginBottom: "6px",
                    }}
                  >
                    Line {annotation.line}
                  </div>
                  <div style={{ color: "#555" }}>{annotation.comment}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const downloadFile = useCallback(() => {
    const element = document.createElement("a");
    const file = new Blob([studentCode], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = "student_code.txt";
    document.body.appendChild(element);
    element.click();
  }, [studentCode]);

  if (isLoading) {
    return <p>Loading...</p>;
  }

  if (!testResults || !Array.isArray(testResults.tests)) {
    return <p>No data available or data is malformed.</p>;
  }

  const displayTests = () => (
    <div>
      <h2>Autograder Results</h2>
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {testResults.tests.map((test, index) => (
          <div
            key={index}
            style={{
              padding: "8px",
              border: "1px solid #ddd",
              background: test.status === "passed" ? "#e6ffed" : "#ffe6e6",
              color: test.status === "passed" ? "green" : "red",
              fontWeight: "bold",
            }}
          >
            {test.name} ({test.score}/{test.max_score})
          </div>
        ))}
      </div>
    </div>
  );

  const displayCode = () => (
    <div>
      <h2>Submitted Code with Annotations</h2>
      <Collapse accordion>
        <Panel header={studentFileName} key="1">
          {displayCodeWithAnnotations()}
          {renderAiFeedbackSummary()}
          {/* <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{studentCode}</pre> */}
          <Button onClick={downloadFile} type="primary" style={{ marginTop: "10px" }}>
            Download
          </Button>
        </Panel>
      </Collapse>
    </div>
  );

  // const

  // Build Content first
  const Content = (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
      <div style={{ flex: 1, minWidth: "60%" }}>{viewMode === "Results" ? displayTests() : displayCode()}</div>
      <div style={{ marginLeft: "20px", flex: "0 1 auto" }}>
        <StudentInfoPanel assignmentName={assignmentName} studentName={studentName} score={StudScore} totalPoints={totalPoints} active={true} onGradeUpdate={fetchSubmissionDetails}/>
      </div>
    </div>
  );

  if (isLoading) {
    return <p>Loading...</p>;
  }

  if (!testResults || !Array.isArray(testResults.tests)) {
    return <p>No data available or data is malformed.</p>;
  }

  // Instead of returning just <div>...</div> like you are doing now
  return isModal ? (
    <Modal
      open={true}
      title="Test Results"
      footer={null}
      onCancel={onCancel} // click outside or X to close and go back
      width="80%"
    >
      {Content}
    </Modal>
  ) : (
    Content
  );
};

export default TestResultsDisplay;
