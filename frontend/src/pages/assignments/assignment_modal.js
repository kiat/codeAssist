import { Button, message, Form, Modal, Upload } from "antd";
import { InboxOutlined } from '@ant-design/icons';

export default function AssignmentModal({ open, onCancel, submit }) {

    const { Dragger } = Upload;
    const props = {
      name: 'file',
      multiple: true,
      // action: 'https://www.mocky.io/v2/5cc8019d300000980a055e76',
      onChange(info) {
        const { status } = info.file;
        if (status !== 'uploading') {
          console.log(info.file, info.fileList);
        }
        if (status === 'done') {
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
      console.log('Upload event: ', e);
      if (Array.isArray(e)) {
        return e;
      }
     return e && e.fileList;
    }

    const submitAssignment = async (fileList) => {
      console.log(fileList)
    }

    return (
        <Modal title="Submit Assignment" open={open} onCancel={onCancel} footer={null}>
          <Form layout="vertical" onFinish={submitAssignment}>
            <Form.Item name="upload" getValueFromEvent={getFile}>
              <Dragger {...props}>
                <p className="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p className="ant-upload-text">Click or drag file to this area to upload</p>
                <p className="ant-upload-hint">
                  Support for a single or bulk upload.
                </p>
              </Dragger>
            </Form.Item>
            <Form.Item>
              <Button style={{ width: "100%" }} type="primary" htmlType="submit">
                Submit
              </Button>
            </Form.Item>
          </Form>
        </Modal>
    );
}