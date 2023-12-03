import {
  CheckOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
  ReloadOutlined,
  UploadOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Collapse,
  PageHeader,
  Radio,
  Space,
  Table,
  Typography,
} from "antd";
import axios from "axios";
import { useContext } from "react";
import { useCallback, useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { GlobalContext } from "../../App";
import PageBottom from "../../components/layout/pageBottom";
import PageContent from "../../components/layout/pageContent";
import UploadModal from "../../components/UploadModal";
import { getAssignment } from "../../services/assignment";
import {
  // updateSubmission,
  uploadSubmission,
} from "../../services/assignmentResult";
import { formattingData } from "./constant";
import FormattingModal from "./FormattingModal";

import "./index.css";
import SubmissionHistoryModal from "./submissionHistoryModal";

/**
 * assignment result modal
 * @returns
 */
export default function AssignmentResult() {
  const [pageHeaderTitle, setPageHeaderTitle] = useState("Autograder Results");
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [assignment, setAssignment] = useState({});
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  const { assignmentId } = useParams();
  const location = useLocation();
  const { userInfo, assignmentInfo } = useContext(GlobalContext);
  const [formattingModalOpen, setFormattingOpen] = useState(false);
  const [formattingSelected, setFormattingSelected] = useState([1, 3]);
  const [autoGraderPoints, setAutograderPoints] = useState(0);
  const [results, setResults] = useState([]);
  const [code, setCode] = useState("");
  const [latestSubmission, getLatestSubmission] = useState({ tests: [] });
  const [latestCode, getLatestCode] = useState(null);


  const formattingSelectedUpdate = useCallback((value) => {
    setFormattingSelected(value);
  }, []);

  const toggleFormattingModalOpen = useCallback(() => {
    setFormattingOpen((t) => !t);
  }, []);

  // control assignment history window modal
  const toggleHistoryModalOpen = useCallback(() => {
    setHistoryModalOpen((bool) => !bool);
  }, []);

  // control assignment upload window modal
  const toggleUploadModalOpen = useCallback(() => {
    setUploadModalOpen((bool) => !bool);
  }, []);

  // TODO: remove hardcoded
  const getAssignmentResult = () => {
    fetch(
      process.env.REACT_APP_API_URL + "/get_latest_submission?" +
      new URLSearchParams({
        student_id: userInfo.id,
        assignment_id: assignmentId,
      })
    )
      .then((response) => response.json())
      .then((data) => {
        if (data[0].completed) {
          setResults((prev) => [...prev, data[0]]);
          getLatestSubmission(JSON.parse(data[0].results)); // Store the entire object
          getLatestCode(data[0].student_code_file);
        }
      });

  };

  // update assignment information
  const updateAssignment = useCallback(
    (file, onError, onSuccess) => {
      // getAssignmentResult();
      const formData = new FormData();
      formData.append("file", file);
      formData.append("student_id", userInfo?.id);
      formData.append("assignment_id", assignmentId);
      uploadSubmission(formData)
        .then((res) => {
          setCode(res?.data?.student_code_file);
          // setResults(JSON.parse(res?.data?.results));
          setResults(JSON.parse(JSON.parse(res?.data?.results)));
          onSuccess(res.data, file);
          toggleUploadModalOpen();
        })
        .catch(onError);
    },
    [assignmentId, toggleUploadModalOpen, userInfo?.id]
  );

  const radioChange = useCallback((e) => {
    setPageHeaderTitle(e.target.value);
  }, []);

  useEffect(() => {
    const getAutoGraderPoints = async () => {
      getAssignment({ assignment_id: assignmentId }).then((res) => {
        setAutograderPoints(res.data.autograder_points);
      });
    };
    getAssignmentResult();
    getAutoGraderPoints();
  }, [assignmentId, location.key]);

  const formattingColumns = [
    {
      title: "",
      dataIndex: "id",
      render: (text) =>
        formattingSelected.includes(text) ? <CheckOutlined /> : null,
    },
    { title: "points", dataIndex: "points" },
    { title: "description", dataIndex: "description" },
  ];


  /**
   * Used to display the results json on the results tab
   *
   */
  function DisplayJsonResults({ jsonData }) {
    // Check if jsonData is undefined or if tests is not an array
    if (!jsonData || !Array.isArray(jsonData.tests)) {
      console.log('jsonData:', jsonData);
      return <p>Data is loading or not available...</p>;
    }

    return (
      <div>
        <h2>Tests</h2>
        {/* Since we checked above, we can safely use map on jsonData.tests */}
        {jsonData.tests.map((test, index) => (
          <div key={index}>
            <p>Name: {test.name}</p>
            <p>Score: {test.score}/{test.max_score}</p>
            <p>Status: {test.status}</p>
            {/* Render output if it exists */}
            {test.output && <pre>{test.output}</pre>}
          </div>
        ))}

        {/* Display Other Details with safe access using optional chaining */}
        <h2>Other Details</h2>
        <p>Visibility: {jsonData.visibility}</p>
        <p>Execution Time: {jsonData.execution_time}</p>
        <p>Total Score: {jsonData.score}</p>
      </div>
    );
  }

  const passedTests = latestSubmission.tests.filter(test => test.status === 'passed');
  const failedTests = latestSubmission.tests.filter(test => test.status !== 'passed');

  return (
    <>
      <PageContent>
        {/* <div style={{ display: "flex", flexWrap: "wrap" }}> */}
        <div style={{ display: "flex" }}>
          <div
            style={{
              flex: "1",
              height: "calc(100vh - 40px)",
            }}
          >
            <PageHeader
              style={{ borderBottom: "1px solid #f0f0f0" }}
              title={pageHeaderTitle}
              extra={[
                <Button
                  key={1}
                  onClick={toggleUploadModalOpen}
                  style={{
                    display:
                      assignment.isUpdate && userInfo?.isStudent
                        ? "inline"
                        : "none",
                  }}
                >
                  upload
                </Button>,
                <Radio.Group
                  key={2}
                  buttonStyle="solid"
                  defaultValue="Autograder Results"
                  onChange={radioChange}
                >
                  <Radio.Button value="Autograder Results">
                    Results
                  </Radio.Button>
                  <Radio.Button value="Submitted Files">Code</Radio.Button>
                </Radio.Group>,
              ]}
            />
            <Card bordered={false}>
              
                {pageHeaderTitle === "Autograder Results" && latestSubmission ? (
                  <div>

                    <div>
                      <DisplayJsonResults jsonData={latestSubmission} />
                    </div>

                  </div>
                ) : (
                  <div>

                    <pre>{latestCode}</pre>
                  </div>
                )}
    
            </Card>
            <div
              style={{
                height: "40px",
                backgroundColor: "#1890ff",
                position: "fixed",
                bottom: 0,
                width: "100%",
                marginLeft: "-1px",
              }}
            />
          </div>
          <div
            style={{
              width: "430px",
              paddingLeft: "30px",
              paddingTop: "20px",
              height: "100vh",
            }}
          >
            <Space direction="vertical" size="middle">
              <div>
                <Typography.Title level={5}>STUDENT</Typography.Title>
                <Typography.Text>
                  {assignmentInfo?.studentName ?? userInfo?.name}
                </Typography.Text>
              </div>
              <div>
                <Typography.Title level={5}>AUTOGRADER SCORE</Typography.Title>
                <Typography.Title
                  level={4}
                  style={{ marginTop: "-15px", fontWeight: "700" }}
                >
                  {/* {assignment.score} */}
                  <span>{results[results.length - 1]?.score ?? "..."}</span>
                  <span>/</span>
                  <span>{autoGraderPoints}</span>
                </Typography.Title>
              </div>
              <div>
                {/* I did not test if the failed tests works yet */}
                <Typography.Title level={5}>FAILED TESTS</Typography.Title>
                {failedTests.map((test, index) => (
                  <div key={index} style={{ color: "red" }}>
                    <span>{test.name}</span>
                    <span>{` (${test.score}/${test.max_score})`}</span>
                  </div>
                ))}
              </div>
              <div>
                <Typography.Title level={5}>PASSED TESTS</Typography.Title>
                {passedTests.map((test, index) => (
                  <div key={index} style={{ color: "#20716a" }}>
                    <span>{test.name}</span>
                    <span>{` (${test.score}/${test.max_score})`}</span>
                  </div>
                ))}
              </div>
              <div>
                <div style={{ lineHeight: "30px" }}>
                  <span style={{ fontSize: "18px", fontWeight: 600 }}>
                    formatting
                  </span>
                  <span style={{ float: "right" }}>10.0/10.0 pts</span>
                </div>
                <Table
                  rowKey="id"
                  columns={formattingColumns}
                  // dataSource={formattingData}
                  dataSource={assignment.formattingData}
                  size="small"
                  showHeader={false}
                  // rowSelection={{}}
                  pagination={false}
                />
              </div>
            </Space>

            {/* <h3>PASSED TESTS</h3> */}
            {/* {assignment.results?.map(item => (
          <p key={item.id} style={{ color: "#20716a" }}>
            {item.name}
          </p>
        ))} */}
            {/* <div
              style={{
                position: "fixed",
                bottom: "0px",
                // backgroundColor: "#1ca0a0",
                backgroundColor: "#1890ff",
                lineHeight: "40px",
                width: "100%",
              }}
            >
              <Button
                icon={<ClockCircleOutlined />}
                style={{
                  marginRight: "10px",
                  marginLeft: "15px",
                }}
                // className='right-bottom-but'
                onClick={toggleHistoryModalOpen}
              >
                Submission History
              </Button>
              <Button
                icon={<DownloadOutlined />}
                // className='right-bottom-but'
                download='submission'
                href='http://localhost:3000/static/js/bundle.js'
              >
                Download Submission
              </Button>
            </div> */}
          </div>
          <UploadModal
            title="UPLOAD"
            // url='/api/uploadFile'
            // data={{ assignmentId }}
            open={uploadModalOpen}
            onCancel={toggleUploadModalOpen}
            afterUpdate={updateAssignment}
          />
          <SubmissionHistoryModal
            open={historyModalOpen}
            onCancel={toggleHistoryModalOpen}
          />
        </div>
      </PageContent>
      <PageBottom>
        <Space>
          <Button icon={<ReloadOutlined />}>Rerun Autograder</Button>
          {!userInfo?.isStudent ? (
            <Button onClick={toggleFormattingModalOpen}>Grades</Button>
          ) : null}

          <Button
            icon={<ClockCircleOutlined />}
            // style={{
            //   marginRight: "10px",
            //   marginLeft: "15px",
            // }}
            // className='right-bottom-but'
            onClick={toggleHistoryModalOpen}
          >
            Submission History
          </Button>
          <Button
            icon={<DownloadOutlined />}
            // className='right-bottom-but'
            download="submission"
            href="http://localhost:3000/static/js/bundle.js"
          >
            Download Submission
          </Button>
          <Button>
            <span>Resubmit</span>
            <UploadOutlined />
          </Button>
        </Space>
      </PageBottom>
      <FormattingModal
        open={formattingModalOpen}
        onCancel={toggleFormattingModalOpen}
        formattingData={assignment.formattingData}
        formattingSelectedUpdate={formattingSelectedUpdate}
        formattingSelected={formattingSelected}
      />
    </>
  );
}
