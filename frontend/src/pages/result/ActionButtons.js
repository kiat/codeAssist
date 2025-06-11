import { Button, Space } from "antd";
import { ReloadOutlined, UploadOutlined, DownloadOutlined, ClockCircleOutlined } from "@ant-design/icons";

export default function ActionButtons({ onRerun, onUpload, onDownload, onHistoryOpen, isStudent }) {
  return (
    <Space>
      <Button icon={<ReloadOutlined />} onClick={onRerun}>Rerun Autograder</Button>
      {!isStudent && (
        <Button onClick={onUpload}>Grades</Button>
      )}
      <Button icon={<ClockCircleOutlined />} onClick={onHistoryOpen}>Submission History</Button>
      <Button icon={<DownloadOutlined />} onClick={onDownload}>Download Submission</Button>
      <Button onClick={onUpload}>
        Resubmit
        <UploadOutlined />
      </Button>
    </Space>
  );
}
