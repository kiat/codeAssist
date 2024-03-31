import { ClockCircleOutlined, DownloadOutlined } from "@ant-design/icons";
import { Button, PageHeader, Radio } from "antd";
import { useCallback, useState } from "react";

export default function AssignmentResult() {
  const [pageHeaderTitle, setPageHeaderTitle] = useState("Autograder Results");

  const radioChange = useCallback((e) => {
    setPageHeaderTitle(e.target.value);
  }, []);

  return (
    <div>
      <PageHeader
        title={pageHeaderTitle}
        extra={[
          <Radio.Group
            key="results-code-radio-group"
            buttonStyle="solid"
            defaultValue="Autograder Results"
            onChange={radioChange}
          >
            <Radio.Button value="Autograder Results">Results</Radio.Button>
            <Radio.Button value="Submitted Files">Code</Radio.Button>
          </Radio.Group>,
        ]}
      />
      <div
        style={{
          position: "fixed",
          bottom: "0px",
          width: "100%",
          backgroundColor: "#1890ff",
          textAlign: "center",
        }}
      >
        <Button
          icon={<ClockCircleOutlined />}
          onClick={() => {/* function to handle Submission History */}}
        >
          Submission History
        </Button>
        <Button
          icon={<DownloadOutlined />}
          onClick={() => {/* function to handle Download Submission */}}
        >
          Download Submission
        </Button>
        {/* Additional buttons for Rerun Autograder and Resubmit can go here */}
      </div>
    </div>
  );
}
