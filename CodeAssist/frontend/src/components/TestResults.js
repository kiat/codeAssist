import React from "react"
import TestResult from "./TestResult"

const TestResults = ({ data }) => {
    const tests = data["tests"]

    const { score } = data;
    const maxScore = tests.map((test) => test["max_score"]).reduce((x, y) => x+y, 0.0);

    return (
        <div id="results">
            <h2>Score: {score}/{maxScore}</h2>
            {tests.map((test, index) => {
                const {name, score, max_score, output} = test;
                const title = `${name} (${score}/${max_score})`
                return (
                    <TestResult key={index} testName={title} testOutput={output} />
                )
            })}
        </div>
    )
}

export default TestResults