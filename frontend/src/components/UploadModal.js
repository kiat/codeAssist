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
          // console.log("obj", obj);
          afterUpdate(file, onError, onSuccess);
          // console.log("file", file);
          // console.log("onSuccess", onSuccess);
          // console.log("onError", onError);
        }}
        // upload address
        // action={url}
        // data={data}
        // onChange={info => {
        //   console.log("info", info);
        //   if (info.file.status === "done") {
        //     afterUpdate();
        //   } else if (info.file.status === "error") {
        //     message.error(`${info.file.name} file upload failed`);
        //   }
        // }}
      >
        <Button>Click to Uplaod</Button>
      </Upload>
    </Modal>
  );
}
