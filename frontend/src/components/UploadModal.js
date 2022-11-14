import { Button, message, Modal, Upload } from "antd";

/**
 * 文档上传弹窗组件
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
        // 上传地址
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
