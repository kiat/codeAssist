import { Checkbox, Form, Modal, Radio, Space } from "antd";

export default ({ open, onCancel }) => {
  return (
    <Modal open={open} title='Rubric Options' width={600} onCancel={onCancel}>
      <Form layout='vertical'>
        <Form.Item label='SCORING METHOD'>
          <Radio.Group>
            <Radio value={0}>
              Negative Scoring (points are subtracted from 10.0)
            </Radio>
            <Radio value={1}>Positive Scoring (points are added to 0)</Radio>
          </Radio.Group>
        </Form.Item>
        <Form.Item label='SCORING BOUNDS'>
          <Checkbox.Group>
            <Space direction='vertical'>
              <Checkbox value={0}>Ceiling (maximum score is 10.0)</Checkbox>
              <Checkbox value={1}>Floor (minimum score is 0)</Checkbox>
            </Space>
          </Checkbox.Group>
        </Form.Item>
        <Form.Item label='DEFAULT SCORING SETTINGS'>
          Go to Assignment Settings or Course Settings to change default scoring
          settings.
        </Form.Item>
      </Form>
    </Modal>
  );
};
