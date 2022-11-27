import { Button, message, Modal, Upload } from "antd";

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
        // upload address
        action={url}
        data={data}
        onChange={info => {
          if (info.file.status === "done") {
            afterUpdate();
          } else if (info.file.status === "error") {
            message.error(`${info.file.name} file upload failed`);
          }
        }}
      >
        <Button>Click to Uplaod</Button>
      </Upload>
    </Modal>
  );
}
