import { CheckOutlined, LeftOutlined, RightOutlined } from "@ant-design/icons";
import { Button, Card, Input, PageHeader, Table, Typography } from "antd";
import { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { GlobalContext } from "../../App";
import PageBottom from "../../components/layout/pageBottom";
import PageContent from "../../components/layout/pageContent";
import { formattingData } from "./mock";

export default ({ changePage }) => {
  const { assignmentInfo, updateAssignmentInfo } = useContext(GlobalContext);
  const navigate = useNavigate();

  const goAssignmentResult = name => {
    updateAssignmentInfo({
      ...assignmentInfo,
      studentName: name,
    });
    navigate(`/assignmentResult/${assignmentInfo.id}`);
  };

  const columns = [
    { title: "", render: (text, record, index) => index + 1 },
    {
      title: "USER",
      dataIndex: "user",
      sorter: (a, b) => a.user > b.user,
      render: text => (
        <Typography.Link onClick={() => goAssignmentResult(text)}>
          {text}
        </Typography.Link>
      ),
    },
    {
      title: "LAST GRADED BY",
      dataIndex: "lastGradedBy",
      sorter: (a, b) => a.lastGradedBy > b.lastGradedBy,
    },
    {
      title: "SECTIONS",
      dataIndex: "sections",
      render: text => <Typography.Link>{text}</Typography.Link>,
      sorter: (a, b) => a.sections > b.sections,
    },
    { title: "SCORE", dataIndex: "score", sorter: (a, b) => a.score - b.score },
    {
      title: "GRADED?",
      dataIndex: "graded",
      sorter: (a, b) => a.graded - b.graded,
      render: text => (text ? <CheckOutlined /> : null),
    },
  ];

  return (
    <>
      <PageContent>
        <PageHeader
          title={
            <>
              <Typography.Link onClick={changePage}>
                <LeftOutlined />
              </Typography.Link>
              <span> Question 2: formatting</span>
            </>
          }
          extra={[
            <Input.Search placeholder='Search user' enterButton key={1} />,
          ]}
        />
        <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
          <Table rowKey='id' columns={columns} dataSource={formattingData} />
        </Card>
      </PageContent>
      <PageBottom
        left={
          <span style={{ color: "white", marginLeft: "24px" }}>
            Submissions Graded: 36 out of 36
          </span>
        }
      >
        <Button>
          <span>Grade</span>
          <RightOutlined />
        </Button>
      </PageBottom>
    </>
  );
};
