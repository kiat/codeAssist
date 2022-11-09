// import { ExclamationCircleFilled } from "@ant-design/icons";
import {
  Button,
  Card,
  Descriptions,
  Divider,
  PageHeader,
  Progress,
  Space,
  Table,
} from "antd";
import { tableData, texts } from "./constant";
import TextItem from "./TextItem";
import moment from "moment";
import { Link } from "react-router-dom";

const columns = [
  { title: "ACTIVE ASSIGNMENTS", dataIndex: "assignmentName" },
  {
    title: "RELEASED",
    dataIndex: "released",
    render: text => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
  },
  {
    title: "DUE(CDT)",
    dataIndex: "due",
    render: text => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
  },
  { title: "SUBMISSIONS", dataIndex: "submissions" },
  {
    title: "% GRADED",
    dataIndex: "graded",
    render: text => <Progress percent={text} size='small' status='normal' />,
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
  { title: "REGRAEDS", dataIndex: "regrades" },
];

export default function InstructorDashboard() {
  return (
    <>
      {/* <div>
        <h1>C S N313E</h1>
        <Space>
          <span>Summer 2022</span>
          <span>Course ID: 394120</span>
        </Space>
      </div> */}
      <PageHeader title='C S N313E' subTitle='Summer 2022'>
        <Descriptions>
          <Descriptions.Item label='Course ID'>394120</Descriptions.Item>
        </Descriptions>
      </PageHeader>
      <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
        <h3>DESCRIPTION</h3>
        <Divider style={{ marginTop: 0, marginBottom: "5px" }} />
        <div>
          <span>Edit your course descrption on the </span>
          {/* <Typography.Link>Course Settings</Typography.Link> */}
          <Link to='/courseSettings'>Course Settings</Link>
          <span> page.</span>
        </div>
      </Card>
      <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
        <h3>THINGS TO DO</h3>
        <Divider style={{ marginTop: 0, marginBottom: "5px" }} />
        <Space direction='vertical'>
          {texts.map((item, index) => (
            <TextItem text={item} key={index} />
          ))}
          {/* <div>
            <ExclamationCircleFilled />
            <span> Review and publish grades for </span>
            <Button type='link'>Assignment-0</Button>
            <span>now that you're all done grading.</span>
          </div> */}
        </Space>
      </Card>
      <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
        <Table rowKey='id' columns={columns} dataSource={tableData} />
      </Card>
    </>
  );
}
