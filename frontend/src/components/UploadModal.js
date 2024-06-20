import { Button, Form, message, Modal, Upload } from "antd";
import { InboxOutlined } from '@ant-design/icons';
import { useState } from "react";
// changes made for resubmit functionality
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
  const [file, setFile] = useState(null);

  const handleFileChange = (info) => {
    if (info.file.status === 'done') {
      setFile(info.file.originFileObj);
      message.success(`${info.file.name} file uploaded successfully.`);
    } else if (info.file.status === 'error') {
      message.error(`${info.file.name} file upload failed.`);
    }
  };
  return (
    //working on adding resubmit feature
    <Modal title="Submit Assignment" open={open} onCancel={onCancel} footer={null}>
      <Form layout="vertical">
        <Form.Item name="upload">
          <Upload.Dragger
            name="file"
            multiple={false}
            onChange={handleFileChange}
            beforeUpload={file => {
                setFile(file); // Set file on beforeUpload instead of upload itself
              return false; // Prevent default upload
            }}
            onDrop={e => console.log('Dropped files', e.dataTransfer.files)}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file to this area to upload</p>
          </Upload.Dragger>
        </Form.Item>
        <Form.Item>
          {/* <Button style={{ width: "100%" }} type="primary" onClick={handleSubmit}>
            Submit
          </Button> */}
        </Form.Item>
      </Form>
    </Modal>
    // <Modal
    //   title={title}
    //   open={open}
    //   onCancel={onCancel}
    //   footer={null}
    //   destroyOnClose={true}
    // >
    //   {/* <div style={{ textAlign: "center" }}> */}
    //   <Upload
    //     name='file'
    //     maxCount={1}
    //     customRequest={({ file, onError, onSuccess }) => {
    //       afterUpdate(file, onError, onSuccess);
        
    //     }}>
    //     <Button>Click to Uplaod</Button>
    //   </Upload>
    // </Modal>
  );
}
