import React from 'react';

export default function TestResultsDisplay({ jsonData }) {
  if (!jsonData || !Array.isArray(jsonData.tests)) {
    return <p>Data is loading or not available...</p>;
  }

  const passedTests = jsonData.tests.filter(test => test.status === 'passed');
  const failedTests = jsonData.tests.filter(test => test.status !== 'passed');

  return (
    <div>
      <h2>Passed Tests</h2>
      {passedTests.map((test, index) => (
        <div key={index}>
          <p>Name: {test.name}</p>
          <p>Score: {test.score}/{test.max_score}</p>
          {test.output && <pre>{test.output}</pre>}
        </div>
      ))}

      <h2>Failed Tests</h2>
      {failedTests.map((test, index) => (
        <div key={index}>
          <p>Name: {test.name}</p>
          <p>Score: {test.score}/{test.max_score}</p>
          {test.output && <pre>{test.output}</pre>}
        </div>
      ))}

      <h2>Other Details</h2>
      <p>Visibility: {jsonData.visibility}</p>
      <p>Execution Time: {jsonData.execution_time}</p>
      <p>Total Score: {jsonData.score}</p>
    </div>
  );
}
