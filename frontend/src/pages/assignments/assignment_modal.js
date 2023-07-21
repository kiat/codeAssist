import { Button, message, Form, Modal, Upload } from "antd";
import { InboxOutlined } from '@ant-design/icons';
import { useState } from "react";

export default function AssignmentModal({ open, onCancel, submit, setFile}) {
  const dummyRequest = async ({ file, onSuccess }) => {    
    setTimeout(() => {
       onSuccess("ok");
    }, 0);
  }
    
  const { Dragger } = Upload;
  const props = {
    name: 'file',
    multiple: false,
    customRequest: dummyRequest,
    onChange(info) {
      console.log("Info", info)
      const { status } = info.file;
      if (status !== 'uploading') {
        console.log(info.file, info.fileList);
      }
      if (status === 'done') {
        setFile(info.file)
        message.success(`${info.file.name} file uploaded successfully.`);
      } else if (status === 'error') {
          message.error(`${info.file.name} file upload failed.`);
      }
      },
      onDrop(e) {
        console.log('Dropped files', e.dataTransfer.files);
      },
    };

  const getFile = (e) => {
    console.log("Uploaded", e);
      if (Array.isArray(e)) {
        return e;
      }
     return e && e.fileList;
    }

  return (
    <Modal title="Submit Assignment" open={open} onCancel={onCancel} footer={null}>
      <Form layout="vertical">
        <Form.Item name="upload" getValueFromEvent={getFile}>
          <Dragger {...props}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file to this area to upload</p>
                {/* <p className="ant-upload-hint">
                  Support for a single or bulk upload.
                </p> */}
          </Dragger>
        </Form.Item>
         <Form.Item>
            <Button style={{ width: "100%" }} type="primary" htmlType="submit" onClick = {submit}>
              Submit
            </Button>
          </Form.Item>
      </Form>
    </Modal>
    );
}
