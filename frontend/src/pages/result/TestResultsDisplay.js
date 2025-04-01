import React, { useState, useEffect, useContext } from 'react';
import { Tooltip, Button, Collapse, Spin, Tag } from 'antd';
import { GlobalContext } from '../../App';
import 'antd/dist/antd.css';

const { Panel } = Collapse;

// const AI_FEEDBACK_ENABLED = true;

const TestResultsDisplay = ({ viewMode, studentId, assignmentName, studentName, score, totalPoints, assignmentId, data, aiFeedbackEnabled}) => {
  const { userInfo } = useContext(GlobalContext);
  const [studentCode, setStudentCode] = useState('');
  const [highlightedLines, setHighlightedLines] = useState([]);
  const [annotations, setAnnotations] = useState([]);
  const [loadingStatus, setLoadingStatus] = useState('null'); // 'loading', 'success', 'error', or null
  // const [aiFeedbackEnabled, setAiFeedbackEnabled] = useState(true);

  const getAiAnnotations = () => {
    if (!aiFeedbackEnabled) {
      // setAiFeedbackEnabled(false);
      setLoadingStatus(null);
      return null;
    }
  
    if (data && data.ai_feedback !== undefined && data.ai_feedback !== null) {
      if (typeof data.ai_feedback === 'string') {
        try {
          const parsed = JSON.parse(data.ai_feedback);
          return parsed;
        } catch (error) {
          console.error('Error parsing ai_feedback from JSON:', error);
          setLoadingStatus('error');
          return null;
        }
      } else {
        console.error('AI Feedback is not a string', data.ai_feedback);
        setLoadingStatus('error');
        return null;
      }
    } else {
      // ai_feedback is still being generated or fetched
      console.log("ai_feedback is still being generated or fetched");
      console.log(data, data.ai_feedback);
      setLoadingStatus('loading');
      return null;
    }
  };

  const findAnnotations = (code) => {
    setLoadingStatus('loading');
  
    const aiAnnotations = getAiAnnotations();
    if (!aiAnnotations) {
      setLoadingStatus('loading');
      return;
    }
  
    if (aiAnnotations.error) {
      console.error("AI feedback error:", aiAnnotations.error);
      setLoadingStatus('error');
      return;
    }
  
    const { annotations } = aiAnnotations;
    if (!Array.isArray(annotations)) {
      console.error("Missing or invalid 'annotations' array in AI feedback.");
      setLoadingStatus('error');
      return;
    }

    console.log("Ai annotations: ", annotations)
 
  
    const lines = code.split('\n');
    const highlighted = [];
    const newAnnotations = [];


    const escapeRegExp = (string) =>
      string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole match
  
    annotations.forEach(({ pattern, comment }) => {
      let regex;
      try {
        const safePattern = escapeRegExp(pattern.trim());  // Escape special characters
        regex = new RegExp(safePattern);
      } catch (e) {
        console.warn(`Invalid regex pattern skipped: ${pattern}`, e);
        return;
      }
  
      lines.forEach((line, index) => {
        if (regex.test(line)) {
          highlighted.push(index + 1);
          newAnnotations.push({ line: index + 1, comment });
        }
      });
    });
  
    setHighlightedLines(highlighted);
    setAnnotations(newAnnotations);
    setLoadingStatus('success');
  };

  useEffect(() => {
    if (data) {
      setStudentCode(data.student_code_file || '');
      // setAiFeedbackEnabled(true);
      findAnnotations(data.student_code_file || '');
    }
  }, [data]);

  const displayCodeWithAnnotations = () => {
    const lines = studentCode.split('\n');

    return (
      <div style={{ position: 'relative', maxHeight: '400px', overflowY: 'scroll', border: '1px solid #ccc', padding: '10px' }}>
        {/* Loader/Status only if AI feedback is enabled */}
        {aiFeedbackEnabled && (
  <div style={{ position: 'absolute', top: 5, right: 10, display: 'flex', alignItems: 'center', gap: '8px' }}>
    <Tooltip title="Fetching AI feedback...">
      {loadingStatus === 'loading' && <Spin size="small" />}
    </Tooltip>

    {loadingStatus === 'success' && (
      <Tooltip title="AI feedback was successfully loaded and applied to matching code lines.">
        <Tag color="green">AI Feedback Loaded</Tag>
      </Tooltip>
    )}

    {loadingStatus === 'error' && (
      <Tooltip title="An error occurred while parsing or loading AI feedback. Ensure the backend response is a valid JSON with an 'annotations' array.">
        <Tag color="red">AI Feedback Error</Tag>
      </Tooltip>
    )}
  </div>
)}

        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
          {lines.map((line, index) => {
            const lineNumber = index + 1;
            const isHighlighted = highlightedLines.includes(lineNumber);
            const annotation = annotations.find(a => a.line === lineNumber);

            return (
              <Tooltip key={lineNumber} title={annotation ? annotation.comment : ''}>
                <div
                  style={{
                    backgroundColor: isHighlighted ? '#ffe6e6' : 'transparent',
                    padding: '2px 0',
                    margin: '2px 0',
                    borderLeft: isHighlighted ? '5px solid red' : 'none',
                  }}
                >
                  {line}
                </div>
              </Tooltip>
            );
          })}
        </pre>
        <Button type="primary" style={{ marginTop: '10px' }}>
          Download
        </Button>
      </div>
    );
  };

  return (
    <div>
      <h2>Submitted Code with Annotations</h2>
      <Collapse accordion>
        <Panel header="Student Code" key="1">
          {displayCodeWithAnnotations()}
        </Panel>
      </Collapse>
    </div>
  );
};

export default TestResultsDisplay;
