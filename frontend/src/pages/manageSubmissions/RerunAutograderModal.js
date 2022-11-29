import { ReloadOutlined } from "@ant-design/icons";
import { Modal, Typography } from "antd";

export default ({ open, onCancel }) => {
  return (
    <Modal
      open={open}
      onCancel={onCancel}
      title='Rerun Autograder'
      okText={
        <span>
          <ReloadOutlined />
          <span> Regrade</span>
        </span>
      }
    >
      <Typography.Paragraph>
        You are about to rerun the autograder for all active submissions. This
        will not affect the autograder scores for any previous inactive
        submissions or any manual grading.
      </Typography.Paragraph>
    </Modal>
  );
};
