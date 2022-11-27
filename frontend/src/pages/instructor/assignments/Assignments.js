import { Button, Card, Progress, Table } from "antd";
import moment from "moment";
import { Link } from "react-router-dom";
import { tableData } from "./constant";

const columns = [
  {
    title: "NAME",
    dataIndex: "assignmentName",
    sorter: (a, b) => a.assignmentName > b.assignmentName,
    render: (text, record) => (
      <Link to={`/assignment/reviewGrades/${record.id}`}>{text}</Link>
    ),
  },
  {
    title: "POINTS",
    dataIndex: "points",
    sorter: (a, b) => a.points - b.points,
  },
  {
    title: "RELEASED",
    dataIndex: "released",
    render: text => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
    sorter: (a, b) => a.released - b.released,
  },
  {
    title: "DUE(CDT)",
    dataIndex: "due",
    render: text => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
    sorter: (a, b) => a.due - b.due,
  },
  {
    title: "SUBMISSIONS",
    dataIndex: "submissions",
    sorter: (a, b) => a.submissions - b.submissions,
  },
  {
    title: "% GRADED",
    dataIndex: "graded",
    render: text => <Progress percent={text} size='small' status='normal' />,
    sorter: (a, b) => a.graded - b.graded,
  },
  {
    title: "PUBLISHED",
    dataIndex: "published",
    render: text => (
      <Button type={text ? "primary" : "default"} shape='circle' size='small'>
        {" "}
      </Button>
    ),
  },
  { title: "REGRADES", dataIndex: "regrades" },
];

export default ({ toggleIsCreate }) => {
  return (
    <>
      <Card bordered={false}>
        <Table rowKey='id' columns={columns} dataSource={tableData} />
      </Card>

      {/* <Modal
        title='Duplicate an Assignment'
        open={createAssignmentModal}
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
      </Modal> */}
    </>
  );
};
