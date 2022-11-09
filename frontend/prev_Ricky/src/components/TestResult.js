import React from "react";

const TestResult = ({ colorClass, testName, testOutput }) => {
	return (
		<div className="testResultBox">
			<h3 className={colorClass}>{testName}</h3>
			{testOutput && <p>{testOutput}</p>}
		</div>
	);
};

export default TestResult;
