import {
  Button,
  Card,
  Input,
  PageHeader,
  Space,
  Table,
  Typography,
} from "antd";
import { formatDayTimeEn } from "../../common/format";
import PageContent from "../../components/layout/pageContent";
import { tableData } from "./mock";
import {
  CloseOutlined,
  ReloadOutlined,
  RightOutlined,
} from "@ant-design/icons";
import PageBottom from "../../components/layout/pageBottom";
import RerunAutograderModal from "./RerunAutograderModal";
import { useContext, useState } from "react";
import { useCallback } from "react";
import { GlobalContext } from "../../App";
import { useNavigate } from "react-router-dom";

export default () => {
  const [rerunModalOpen, setRerunModalOpen] = useState(false);
  const { assignmentInfo, updateAssignmentInfo } = useContext(GlobalContext);
  const navigate = useNavigate();

  const toggleRerunModalOpen = useCallback(() => {
    setRerunModalOpen(t => !t);
  }, []);

  const goAssignmentResult = name => {
    updateAssignmentInfo({
      ...assignmentInfo,
      studentName: name,
    });
    navigate(`/assignmentResult/${assignmentInfo.id}`);
  };

  const columns = [
    {
      title: "NAME",
      dataIndex: "name",
      render: text => (
        <Typography.Link onClick={() => goAssignmentResult(text)}>
          {text}
        </Typography.Link>
      ),
      sorter: (a, b) => a.name > b.name,
    },
    {
      title: "SUBMISSION TIME (CST)",
      dataIndex: "submissionTime",
      render: text => formatDayTimeEn(text),
      sorter: (a, b) => a.submissionTime - b.submissionTime,
    },
    {
      title: "SCORE",
      dataIndex: "score",
      align: "center",
      sorter: (a, b) => a.score - b.score,
    },
    {
      title: "DELETE",
      align: "center",
      render: text => (
        <Button danger type='primary' size='small' icon={<CloseOutlined />} />
      ),
    },
  ];
  return (
    <>
      <PageContent>
        <PageHeader
          title='Manage Submissions'
          extra={[
            <Input.Search
              // style={{ width: "300px", marginLeft: "24px" }}
              placeholder='Search name'
              // suffix={<SearchOutlined />}
              enterButton
              key={1}
            />,
          ]}
        />
        {/* <Input.Search
          style={{ width: "300px", marginLeft: "24px" }}
          placeholder='Search name'
          // suffix={<SearchOutlined />}
          enterButton
        /> */}
        <Card
          bordered={false}
          bodyStyle={{ paddingTop: 0 }}
          // extra={<Input.Search placeholder='Search NAME' />}
        >
          <Table
            rowKey='id'
            columns={columns}
            dataSource={tableData}
            // title={() => (
            //   <Input.Search
            //     style={{ width: "300px" }}
            //     placeholder='Search name'
            //     // suffix={<SearchOutlined />}
            //     enterButton
            //   />
            // )}
          />
        </Card>
      </PageContent>
      <PageBottom>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={toggleRerunModalOpen}>
            Regrade All Submissions
          </Button>
          <Button>
            <span>Grade Submissions</span>
            <RightOutlined />
          </Button>
        </Space>
      </PageBottom>
      <RerunAutograderModal
        open={rerunModalOpen}
        onCancel={toggleRerunModalOpen}
      />
    </>
  );
};
