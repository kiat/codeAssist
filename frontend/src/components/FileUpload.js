import React from "react";
import { useState } from "react";
import axios from "axios";
import TestResults from "./TestResults";
import TestResult from "./TestResult";

const FileUpload = () => {
	const [file, setFile] = useState(null);
	const [response, setResponse] = useState(null);
	const [logs, setLogs] = useState(null);
	const [assignment, setAssignment] = useState("A1");

	const uploadFile = async (e) => {
		e.preventDefault();
		const data = new FormData();

		data.append("file", file);
		data.append("assignment", assignment);
		const url = process.env.REACT_APP_API_URL + "/upload";
		const response = await axios.post(url, data, {});
		setResponse(JSON.parse(response.data["results"]));
		setLogs(response.data["logs"]);
		console.log("got results and logs");
	};

	return (
		<div>
			<div id="form">
				<form onSubmit={uploadFile} encType="multipart/form-data">
					<div id="dockerfile">
						<p className="inline">Select assignment</p>
						<select
							className="inline"
							value={assignment}
							onChange={(e) => setAssignment(e.target.value)}
						>
							<option value="test">test</option>
							<option value="A1">A1</option>
						</select>
					</div>
					<div id="file">
						<p className="inline">Choose file</p>
						<input
							id="fileUpload"
							type="file"
							name="file"
							onChange={(e) => setFile(e.target.files[0])}
						/>
						<input id="submit" type="submit" />
					</div>
				</form>
			</div>
			<div>
				<h1>Results</h1>
				{response && <TestResults data={response} />}
			</div>
			<div>
				<h1>Logs</h1>
				{logs && (
					<TestResult
						colorClass={""}
						testName={"Log Output"}
						testOutput={logs}
					/>
				)}
			</div>
		</div>
	);
};

export default FileUpload;
