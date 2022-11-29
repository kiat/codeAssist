import {
  CheckOutlined,
  DownloadOutlined,
  EyeOutlined,
  RightOutlined,
} from "@ant-design/icons";
import { Button, PageHeader, Space, Table, Typography } from "antd";
import { useState, useEffect } from "react";
import { formatDayTimeEn } from "../../common/format";
import { GRADES } from "./mock";
import PageBottom from "../../components/layout/pageBottom";
import PageContent from "../../components/layout/pageContent";
import PopoverDownload from "../../components/download/PopoverDownload";
import DownloadSubmissions from "./DownloadSubmissions";
import { useCallback } from "react";
import { useContext } from "react";
import { GlobalContext } from "../../App";
import { useNavigate } from "react-router-dom";
// import { useParams } from "react-router-dom";

export default () => {
  const [assignmentDetail, setAssignmentDetail] = useState();
  const [downloadModalOpen, setDownloadModalOpen] = useState(false);
  const { assignmentInfo, updateAssignmentInfo } = useContext(GlobalContext);
  const navigate = useNavigate();
  // const {} = useParams();
  // const { assignmentId } = useParams();
  // const [searchParams] = useSearchParams();
  // console.log("assignmentId", assignmentId);
  // console.log("searchParams", searchParams);

  const toggleDownloadModalOpen = useCallback(() => {
    setDownloadModalOpen(t => !t);
  }, []);

  // const getAssignmentInfo = () => {
  //   updateAssignmentInfo({
  //     name: "Assignment-11",
  //   });
  //   setAssignmentInfo({
  //     name: "Assignment-11",
  //     grades: GRADES,
  //   });
  // };

  useEffect(() => {
    // if (!assignmentInfo.id) {
    //   updateAssignmentInfo({
    //     // name: "Assignment-11",
    //     id: assignmentId,
    //     name: "Training-Test-2-Question-1 - Gift Card",
    //   });
    // }
    setAssignmentDetail({
      // name: "Training-Test-2-Question-1 - Gift Card",
      grades: GRADES,
    });
  }, []);

  const sharedCell = record => {
    if (record.score) {
      return {};
    }
    return {
      colSpan: 0,
    };
  };

  const goAssignmentResult = name => {
    updateAssignmentInfo({
      ...assignmentInfo,
      studentName: name,
    });
    navigate(`/assignmentResult/${assignmentInfo.id}`);
  };

  const columns = [
    {
      title: "FIRST & LAST NAME",
      dataIndex: "username",
      render: text => (
        <Typography.Link onClick={() => goAssignmentResult(text)}>
          {text}
        </Typography.Link>
      ),
      sorter: (a, b) => a.username > b.username,
    },
    {
      title: "EMAIL",
      dataIndex: "email",
      render: text => <Typography.Link>{text}</Typography.Link>,
      sorter: (a, b) => a.email > b.email,
    },
    {
      title: "SCORE/100",
      dataIndex: "score",
      align: "center",
      onCell: record => {
        if (record.score) {
          return {};
        } else {
          return {
            colSpan: 4,
          };
        }
      },
      render: text => (text ? text : "This student doesn't have a submission."),
      sorter: (a, b) => a.score - b.score,
    },
    {
      title: "GRADED",
      dataIndex: "graded",
      align: "center",
      render: text => (
        <CheckOutlined style={{ color: text ? "#189eff" : "" }} />
      ),
      onCell: sharedCell,
      sorter: (a, b) => a.graded - b.graded,
    },
    {
      title: "VIEWED",
      dataIndex: "viewed",
      align: "center",
      render: text => <EyeOutlined style={{ color: text ? "#189eff" : "" }} />,
      onCell: sharedCell,
      sorter: (a, b) => a.viewed - b.viewed,
    },
    // { title: "CANVAS", dataIndex: "canvas" },
    {
      title: "TIME(CST)",
      dataIndex: "time",
      render: text => formatDayTimeEn(text),
      onCell: sharedCell,
      sorter: (a, b) => a.time - b.time,
    },
  ];

  return (
    <>
      <PageContent>
        <PageHeader title={`Review Grades for ${assignmentInfo?.name}`} />
        <Table
          columns={columns}
          dataSource={assignmentDetail?.grades}
          rowKey='id'
          style={{ marginLeft: "10px" }}
        />
      </PageContent>
      <PageBottom>
        <Space>
          {/* <Button icon={<DownloadOutlined />}>Download Grades</Button> */}
          <PopoverDownload />
          <Button icon={<DownloadOutlined />} onClick={toggleDownloadModalOpen}>
            Export Submissions
          </Button>
          <Button icon={<RightOutlined />}>Publish Grades</Button>
        </Space>
      </PageBottom>
      <DownloadSubmissions
        open={downloadModalOpen}
        onCancel={toggleDownloadModalOpen}
      />
    </>
  );
};
