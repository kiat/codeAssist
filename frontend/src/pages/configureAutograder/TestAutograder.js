import { Button, Form, Modal, Radio, Select, Typography, Upload } from "antd";

export default ({ open, onCancel }) => {
  return (
    <Modal
      open={open}
      title='Submit Programming Assignment'
      onCancel={onCancel}
    >
      <Form layout='vertical'>
        <Form.Item label='SUBMISSION METHOD' name='submissionMethod'>
          <Radio.Group
            defaultValue={0}
            options={[
              { label: "Upload", value: 0 },
              { label: "GitHUb", value: 1 },
              { label: "Bitbucket", value: 2 },
            ]}
          />
        </Form.Item>
        <Form.Item
          noStyle
          shouldUpdate={(pv, cv) => pv.submissionMethod !== cv.submissionMethod}
        >
          {({ getFieldValue }) => {
            switch (getFieldValue("submissionMethod")) {
              case 2:
                return (
                  <>
                    <Form.Item label='CONNECT YOUR ACCOUNT'>
                      <Button>Connect to Bitbucket</Button>
                    </Form.Item>
                    <Form.Item label='REPOSITORY' name='repository'>
                      <Select placeholder='Select a repository' />
                    </Form.Item>
                    <Form.Item label='BRANCH' name='branch'>
                      <Select placeholder='Select a branch' />
                    </Form.Item>
                  </>
                );
              case 1:
                return (
                  <>
                    <Form.Item label='REPOSITORY' name='repository'>
                      <Select placeholder='Select a repository' />
                    </Form.Item>
                    <Form.Item label='BRANCH' name='branch'>
                      <Select placeholder='Select a branch' />
                    </Form.Item>
                  </>
                );
              default:
                return (
                  <Upload.Dragger>
                    <div>
                      <Typography.Title level={4}>Drag & Drop</Typography.Title>
                      <Typography.Paragraph>
                        Any file(s) including .zip. Click to browse .
                      </Typography.Paragraph>
                    </div>
                  </Upload.Dragger>
                );
            }
          }}
        </Form.Item>
      </Form>
    </Modal>
  );
};
