import { Button, Space } from "antd";
import { ReloadOutlined, UploadOutlined, DownloadOutlined, ClockCircleOutlined, CodeOutlined } from "@ant-design/icons";

export default function ActionButtons({
  onRerun,
  onUpload,
  onResubmitEditor,
  onDownload,
  onHistoryOpen,
  isStudent,
  allowFileUpload = true,
  enableCodeEditor,
  rerunLoading = false,
}) {
  return (
    <Space wrap>
      <Button icon={<ReloadOutlined />} loading={rerunLoading} onClick={onRerun}>
        Rerun Autograder
      </Button>
      {!isStudent && (
        <Button onClick={onUpload}>Grades</Button>
      )}
      <Button icon={<ClockCircleOutlined />} onClick={onHistoryOpen}>Submission History</Button>
      <Button icon={<DownloadOutlined />} onClick={onDownload}>Download Submission</Button>
      {allowFileUpload && (
        <Button icon={<UploadOutlined />} onClick={onUpload}>
          Resubmit via Upload
        </Button>
      )}
      {enableCodeEditor && (
        <Button icon={<CodeOutlined />} onClick={onResubmitEditor}>
          Resubmit via Editor
        </Button>
      )}
    </Space>
  );
}
