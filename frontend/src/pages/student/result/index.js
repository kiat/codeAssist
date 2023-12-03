import { ClockCircleOutlined, DownloadOutlined } from "@ant-design/icons";
import { Button, Card, Collapse, PageHeader, Radio } from "antd";
import axios from "axios";
import { useCallback, useEffect, useState, useContext } from "react";
import { useLocation, useParams } from "react-router-dom";
import UploadModal from "../../../components/UploadModal";
import { GlobalContext } from "../../App";
import "./index.css";
import SubmissionHistoryModal from "./submissionHistoryModal";

export default function AssignmentResult() {
  const [pageHeaderTitle, setPageHeaderTitle] = useState("Autograder Results");
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [assignmentInfo, setAssignmentInfo, userInfo] = useContext(GlobalContext);
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  const { assignmentId } = useParams();
  const location = useLocation();

  const toggleHistoryModalOpen = useCallback(() => {
    setHistoryModalOpen((bool) => !bool);
  }, []);

  const toggleUploadModalOpen = useCallback(() => {
    setUploadModalOpen((bool) => !bool);
  }, []);

  const getAssignmentResult = useCallback(() => {
    const studentId = userInfo?.id;

    const endpointURL = process.env.REACT_APP_API_URL + "/get_results?student_id=${studentId}&assignment_id=${assignmentId}";

    axios.get(endpointURL)
    .then(res => {
      if (res.data && res.data.length > 0) {
        const { results, student_code_file } = res.data[0]; 

        setAssignmentInfo(prevState => ({
          ...prevState,
          results: [{ name: "Results", text: results }],
          codes: [{ name: "Code", text: student_code_file }],
        }));
      }
    })
    .catch(error => {
      console.error("Failed to fetch assignment results:", error);
    });
  }, [assignmentId, userInfo, setAssignmentInfo]);

  useEffect(() => {
    getAssignmentResult();
  }, [location.key, getAssignmentResult]);

  const radioChange = useCallback(
    (e) => {
      setPageHeaderTitle(e.target.value);
    },
    []
  );

  const items = 
    pageHeaderTitle === "Autograder Results" 
      ? assignmentInfo.results 
      : assignmentInfo.codes;

  return (
    <div style={{ display: "flex", flexWrap: "wrap" }}>
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
                display: assignmentInfo.isUpdate ? "inline" : "none",
              }}
            >
              upload
            </Button>,
            <Radio.Group
              key={2}
              buttonStyle='solid'
              defaultValue='Autograder Results'
              onChange={radioChange}
            >
              <Radio.Button value='Autograder Results'>Results</Radio.Button>
              <Radio.Button value='Submitted Files'>Code</Radio.Button>
            </Radio.Group>,
          ]}
        />
        <Card bordered={false}>
          <Collapse
            style={{
              border: "0px",
              backgroundColor: "white",
            }}
          >
            {items?.map(item => (
              <Collapse.Panel
                key={item.name}
                header={<span style={{ color: "#20716a" }}>{item.name}</span>}
                showArrow={false}
                style={{
                  marginBottom: "20px",
                  border: "1px solid #d9d9d9",
                  backgroundColor: "#f9f9fb",
                }}
              >
                {pageHeaderTitle === "Autograder Results" ? (
                <div>
                  <h2>Results</h2>
                  <p>{item.text}</p>
                </div>
              ) : (
                <div>
                  <h2>Code</h2>
                  <pre>{item.text}</pre>
                </div>
              )}
              </Collapse.Panel>
            ))}
          </Collapse>
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
        <h3>AUTOGRADER SCORE</h3>
        <h3>{assignmentInfo.score}</h3>
        <h3>PASSED TESTS</h3>
        {assignmentInfo.results?.map(item => (
          <p key={item.id} style={{ color: "#20716a" }}>
            {item.name}
          </p>
        ))}
        <div
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
        </div>
      </div>
      <UploadModal
        title='UPLOAD'
        url='/api/uploadFile'
        data={{ assignmentId }}
        open={uploadModalOpen}
        onCancel={toggleUploadModalOpen}
        afterUpdate={updateAssignment}
      />
      <SubmissionHistoryModal
        open={historyModalOpen}
        onCancel={toggleHistoryModalOpen}
      />
    </div>
  );
}
