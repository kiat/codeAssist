import React from "react";
import TestResult from "./TestResult";

const getClassNameFromScore = (score, maxScore) => {
	if (score === maxScore) {
		return "testPassed";
	} else if (score === 0) {
		return "testFailed";
	} else {
		return "testPartial";
	}
};

const TestResults = ({ data }) => {
	const tests = data["tests"];

	const { score } = data;
	const maxScore = tests
		.map((test) => test["max_score"])
		.reduce((x, y) => x + y, 0.0);

	return (
		<div id="results">
			<h2>
				Score: {score}/{maxScore}
			</h2>
			{tests.map((test, index) => {
				const { name, score, max_score: maxScore, output } = test;
				const title = `${name} (${score}/${maxScore})`;
				const className = getClassNameFromScore(score, maxScore);
				return (
					<TestResult
						key={index}
						colorClass={className}
						testName={title}
						testOutput={output}
					/>
				);
			})}
		</div>
	);
};

export default TestResults;
