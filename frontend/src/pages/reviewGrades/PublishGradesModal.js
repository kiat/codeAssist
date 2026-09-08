import { useState } from "react";
import { CloseOutlined, SendOutlined } from "@ant-design/icons";
import { Button, Modal, Space, message } from "antd";
import { publishGrades } from "../../services/submission";

export default ({ open, onCancel, assignmentId, published, studentCount, onSuccess }) => {
  const [submitting, setSubmitting] = useState(false);
  const nextPublished = !published;

  const handleConfirm = async () => {
    setSubmitting(true);
    try {
      const res = await publishGrades({
        assignment_id: assignmentId,
        published: nextPublished,
      });
      message.success(
        nextPublished ? "Grades published to students." : "Grades hidden from students."
      );
      onSuccess(res.data);
      onCancel();
    } catch (err) {
      message.error(
        nextPublished ? "Failed to publish grades." : "Failed to unpublish grades."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      open={open}
      title={nextPublished ? "Publish Grades" : "Unpublish Grades"}
      width={470}
      closable={false}
      onCancel={onCancel}
      footer={
        <Button icon={<CloseOutlined />} onClick={onCancel}>
          Close
        </Button>
      }
    >
      <Space style={{ textAlign: "center" }} direction="vertical">
        <div>
          {nextPublished
            ? `Make grades and results visible to all ${studentCount} student${studentCount === 1 ? "" : "s"} on this assignment.`
            : "Hide grades and results from students again. You can re-publish at any time."}
        </div>
        <Button
          shape="round"
          type="primary"
          icon={<SendOutlined />}
          loading={submitting}
          onClick={handleConfirm}
        >
          {nextPublished ? "Publish Grades" : "Unpublish Grades"}
        </Button>
      </Space>
    </Modal>
  );
};
