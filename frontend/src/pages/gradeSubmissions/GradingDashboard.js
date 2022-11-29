import { RightOutlined } from "@ant-design/icons";
import { Button, Card, PageHeader, Progress, Table, Typography } from "antd";
import PageBottom from "../../components/layout/pageBottom";
import PageContent from "../../components/layout/pageContent";
import { gradingData } from "./mock";

export default ({ changePage }) => {
  const columns = [
    {
      title: "QUESTION",
      dataIndex: "question",
      render: text => (
        <Typography.Link onClick={changePage}>{text}</Typography.Link>
      ),
    },
    { title: "POINTS", dataIndex: "points" },
    {
      title: "PROGRESS",
      dataIndex: "progress",
      render: text => <Progress percent={text} status='normal' />,
    },
    { title: "GRADED BY", dataIndex: "gradedBy" },
  ];

  return (
    <>
      <PageContent>
        <PageHeader title='Grading Dashboard' />
        <Card bordered={false}>
          <Table rowKey='id' columns={columns} dataSource={gradingData} />
        </Card>
      </PageContent>
      <PageBottom
        left={
          <span style={{ color: "white", marginLeft: "24px" }}>
            Assignment grading progress: 100%
          </span>
        }
      >
        <Button>
          <span>Review Grades</span>
          <RightOutlined />
        </Button>
      </PageBottom>
    </>
  );
};
