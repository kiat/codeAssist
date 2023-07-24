import {
  Button,
  Checkbox,
  Col,
  Form,
  Input,
  Modal,
  Radio,
  Row,
  Select,
  Space,
} from "antd";

export default ({ open, toggleAddCSVModalOpen, finishCSVForm }) => {
  return (
    <Modal
      open={open}
      title="Add a User With CSV file"
      footer={null}
      onCancel={toggleAddCSVModalOpen}
    >
      <Form layout="vertical" finishCSVForm={finishCSVForm}>
        <Form.Item name="upload">
          {/* <Upload.Dragger
            name="file"
            multiple={false}
            action="http://localhost:5000/upload_submission"
            onChange={handleFileChange}
            beforeUpload={handleBeforeUpload}
            onDrop={e => console.log('Dropped files', e.dataTransfer.files)}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file here to upload CSV File</p>
          </Upload.Dragger> */}
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">
              Submit
            </Button>
            <Button type="primary" danger onClick={toggleAddCSVModalOpen}>
              Cancel
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};
