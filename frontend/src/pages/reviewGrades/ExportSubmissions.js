import { CloseOutlined, DownloadOutlined } from "@ant-design/icons";
import { Button, Modal, Space } from "antd";

export default ({ open, onCancel }) => {
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
          We're exporting your submissions now; this may take a few minutes.
        </div>
        <div>You can check back here in a bit to download the file.</div>
        <div>We'll also email you a link when it's ready.</div>
        <Button shape='round' type='primary' icon={<DownloadOutlined />}>
          Download Submissions
        </Button>
      </Space>
    </Modal>
  );
};
