import React from "react"

const TestResult = ({ testName, testOutput }) => {
    return (
        <div className="testResultBox">
            <h3>{testName}</h3>
            {testOutput && <p>{testOutput}</p>}
        </div>
    )
}

export default TestResult