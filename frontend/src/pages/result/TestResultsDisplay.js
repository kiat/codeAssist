import React, { useContext, useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { GlobalContext } from '../../App';
import { Collapse, Button, Space } from 'antd';
import 'antd/dist/antd.css';
import StudentInfoPanel from "./StudentInfoPanel";

const { Panel } = Collapse;

const TestResultsDisplay = ({ viewMode, studentId, assignmentName, studentName, score, totalPoints }) => {
  const { userInfo, courseInfo } = useContext(GlobalContext);
  const { assignmentId } = useParams();
  const navigate = useNavigate();
  const [testResults, setTestResults] = useState(null);
  const [studentCode, setStudentCode] = useState('');
  const [studentFileName, setStudentFileName] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [StudScore, setStudScore] = useState(score);

  useEffect(() => {
    if (!userInfo || !userInfo.id) {
      navigate('/');
      return;
    }
    if (!assignmentId) {
      console.error('No assignment_id provided');
      return;
    }

    const fetchResults = async () => {
      setIsLoading(true);
      try {
        const send = userInfo.isStudent ? userInfo.id : studentId;
        const response = await fetch(`${process.env.REACT_APP_API_URL}/get_latest_submission?` +
          new URLSearchParams({
            student_id: send,
            assignment_id: assignmentId
          }));

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        if (data.score) {
          setStudScore(data.score);
        }
        if (data.results) {
          const parsedResults = JSON.parse(data.results);
          setTestResults(parsedResults);
          setStudentCode(data.student_code_file);
          setStudentFileName(data.file_name);
        } else {
          throw new Error('Results data is not available');
        }
      } catch (error) {
        setError(error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [assignmentId, navigate, userInfo, courseInfo, studentId]);

  const downloadFile = useCallback(() => {
    const element = document.createElement('a');
    const file = new Blob([studentCode], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = 'student_code.txt';
    document.body.appendChild(element);
    element.click();
  }, [studentCode]);

  if (isLoading) {
    return <p>Loading...</p>;
  }

  if (error) {
    return <p>Error loading data: {error.message}</p>;
  }

  if (!testResults || !Array.isArray(testResults.tests)) {
    return <p>No data available or data is malformed.</p>;
  }

  const displayTests = () => (
    <div>
      <h2>Autograder Results</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {testResults.tests.map((test, index) => (
          <div
            key={index}
            style={{
              padding: '8px',
              border: '1px solid #ddd',
              background: test.status === 'passed' ? '#e6ffed' : '#ffe6e6',
              color: test.status === 'passed' ? 'green' : 'red',
              fontWeight: 'bold'
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
      <h2>Submitted Files</h2>
      <Collapse accordion>
        <Panel header={studentFileName} key="1">
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{studentCode}</pre>
          <Button onClick={downloadFile} type="primary" style={{ marginTop: '10px' }}>
            Download
          </Button>
        </Panel>
      </Collapse>
    </div>
  );

  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div style={{ flex: 1, minWidth: '60%' }}>
        {viewMode === "Results" ? displayTests() : displayCode()}
      </div>
      <div style={{ marginLeft: '20px', flex: '0 1 auto' }}>
        <StudentInfoPanel
          assignmentName={assignmentName}
          studentName={studentName}
          score={StudScore}
          totalPoints={totalPoints}
        />
      </div>
    </div>
  );
};

export default TestResultsDisplay;
