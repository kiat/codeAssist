import { useState } from "react";
import { CloseOutlined, DownloadOutlined } from "@ant-design/icons";
import { Button, Modal, Space, message } from "antd";
import { exportSubmissions } from "../../services/submission";

const DEFAULT_DOWNLOAD_NAME = "submissions.zip";

const getFilenameFromContentDisposition = (headerValue) => {
  if (!headerValue) return DEFAULT_DOWNLOAD_NAME;
  const utf8Match = /filename\*=UTF-8''([^;]+)/i.exec(headerValue);
  const basicMatch = /filename="?([^";]+)"?/i.exec(headerValue);
  const filename = (utf8Match?.[1] || basicMatch?.[1] || "").trim();

  if (!filename) return DEFAULT_DOWNLOAD_NAME;

  try {
    return decodeURIComponent(filename);
  } catch {
    return filename;
  }
};

export default ({ open, onCancel, assignmentId }) => {
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    if (!assignmentId) {
      message.error("Assignment is still loading.");
      return;
    }

    setDownloading(true);
    try {
      const response = await exportSubmissions({ assignment_id: assignmentId });
      const blob = new Blob([response.data], { type: "application/zip" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = getFilenameFromContentDisposition(
        response.headers?.["content-disposition"] ||
          response.headers?.["Content-Disposition"]
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      if (err.response?.data instanceof Blob) {
        try {
          const text = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsText(err.response.data);
          });
          const parsed = JSON.parse(text);
          message.error(parsed.message || "Failed to export submissions.");
        } catch {
          message.error("Failed to export submissions.");
        }
      } else {
        message.error("Failed to export submissions.");
      }
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Modal
      open={open}
      title='Export Submissions'
      width={470}
      closable={false}
      onCancel={onCancel}
      footer={
        <Button icon={<CloseOutlined />} onClick={onCancel}>
          Close
        </Button>
      }
    >
      <Space style={{ textAlign: "center" }} direction='vertical'>
        <div>
          Export every student's active submission and grading results as a
          zip file.
        </div>
        <Button
          shape='round'
          type='primary'
          icon={<DownloadOutlined />}
          loading={downloading}
          onClick={handleDownload}
        >
          Download Submissions
        </Button>
      </Space>
    </Modal>
  );
};
