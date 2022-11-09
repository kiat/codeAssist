import { Button, Form, Input, Modal, Select, Space, Typography } from "antd";

export default ({ open, toggleCreateAssignmentModal }) => {
  return (
    <Modal
      title='Duplicate an Assignment'
      open={open}
      onCancel={toggleCreateAssignmentModal}
      // onOk={() => {
      //   toggleCreateAssignmentModal();
      // }}
      footer={null}
    >
      <Form layout='vertical'>
        <Form.Item
          name='oldAssignment'
          label={
            <div>
              <Typography.Title level={4} style={{ marginBottom: 0 }}>
                C S N313E
              </Typography.Title>
              <Typography.Title level={5} style={{ marginTop: 0 }}>
                SUMMER 2022
              </Typography.Title>
            </div>
          }
        >
          <Select
            style={{ width: "100%" }}
            options={[
              { label: "Assignment-0", value: 0 },
              { label: "Assignment-1", value: 1 },
              { label: "Assignment-2", value: 2 },
              { label: "Assignment-3", value: 3 },
              { label: "Assignment-4", value: 4 },
              { label: "Assignment-5", value: 5 },
            ]}
          />
        </Form.Item>
        <Form.Item label='COPIED ASSIGNMENT TITLE' name='newAssignment'>
          <Input placeholder='e.g. Homework 1' />
        </Form.Item>
      </Form>
      <Form.Item>
        <Space>
          <Button type='primary' onClick={toggleCreateAssignmentModal}>
            Duplicate
          </Button>
          <Button type='primary' danger onClick={toggleCreateAssignmentModal}>
            Cancel
          </Button>
        </Space>
      </Form.Item>
    </Modal>
  );
};
