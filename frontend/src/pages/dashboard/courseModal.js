import { Modal } from "antd";

export default function CourseModal({ title, open, onCancel, children }) {
  return (
    <Modal title={title} open={open} onCancel={onCancel} footer={null}>
      {children}
    </Modal>
  );
}
