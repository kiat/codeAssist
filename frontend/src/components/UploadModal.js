import { Button, Modal, Upload } from "antd";

/**
 * file upload windows modal
 * @param {*} param0
 * @returns
 */
export default function UploadModal({
  open,
  title,
  onCancel,
  afterUpdate,
  url,
  data,
}) {
  return (
    <Modal
      title={title}
      open={open}
      onCancel={onCancel}
      footer={null}
      destroyOnClose={true}
    >
      {/* <div style={{ textAlign: "center" }}> */}
      <Upload
        name='file'
        maxCount={1}
        customRequest={({ file, onError, onSuccess }) => {
          afterUpdate(file, onError, onSuccess);
        
        }}>
        <Button>Click to Uplaod</Button>
      </Upload>
    </Modal>
  );
}
