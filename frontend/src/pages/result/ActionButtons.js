import { Button, Space } from "antd";
import { ReloadOutlined, UploadOutlined, DownloadOutlined, ClockCircleOutlined, CodeOutlined } from "@ant-design/icons";

export default function ActionButtons({ onRerun, onUpload, onResubmitEditor, onDownload, onHistoryOpen, isStudent, enableCodeEditor }) {
  return (
    <Space>
      <Button icon={<ReloadOutlined />} onClick={onRerun}>Rerun Autograder</Button>
      {!isStudent && (
        <Button onClick={onUpload}>Grades</Button>
      )}
      <Button icon={<ClockCircleOutlined />} onClick={onHistoryOpen}>Submission History</Button>
      <Button icon={<DownloadOutlined />} onClick={onDownload}>Download Submission</Button>
      {enableCodeEditor ? (
        <Button type="primary" icon={<CodeOutlined />} onClick={onResubmitEditor}>
          Resubmit via Editor
        </Button>
      ) : (
        <Button onClick={onUpload}>
          Resubmit
          <UploadOutlined />
        </Button>
      )}
    </Space>
  );
}
