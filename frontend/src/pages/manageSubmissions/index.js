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
// import { tableData } from "./mock";
import {
  CloseOutlined,
  ConsoleSqlOutlined,
  ReloadOutlined,
  RightOutlined,
} from "@ant-design/icons";
import PageBottom from "../../components/layout/pageBottom";
import RerunAutograderModal from "./RerunAutograderModal";
import { useContext, useState, useEffect } from "react";
import { useCallback } from "react";
import { GlobalContext } from "../../App";
import { useNavigate } from "react-router-dom";
import moment from "moment";

export default () => {
  const [rerunModalOpen, setRerunModalOpen] = useState(false);
  const { assignmentInfo, updateAssignmentInfo } = useContext(GlobalContext);
  const { courseInfo, updateCourseInfo } = useContext(GlobalContext);
  const [students, setStudents] = useState({});
  const navigate = useNavigate();
  const [tableData, setTableData] = useState([]);
  
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

  useEffect(() => {
    fetch(process.env.REACT_APP_API_URL + "/get_course_enrollment?" + 
      new URLSearchParams({
        course_id: courseInfo.id
      })
    )
    .then(res => res.json())
    .then(data => {
      setStudents(data);
    })
  }, []);

  useEffect(() => {
    if (Object.keys(students).length > 0 && assignmentInfo.id && Object.keys(tableData).length < 1) {
      students.forEach(student => {
        fetch(process.env.REACT_APP_API_URL + "/get_latest_submission?" +
          new URLSearchParams({
            student_id: student.id,
            assignment_id: assignmentInfo.id
          })
        )
        .then(res => res.json())
        .then(data => {
          if (Object.keys(data).length > 0) {
            const submission = {
              name: student.name,
              submissionTime: moment(data[0].executed_at).valueOf(),
              score: data[0].score,
              id: data[0].student_id
            };
            setTableData(prevData => {
              if (prevData.findIndex(obj => obj.id === submission.id) !== -1) return prevData;
              return [...prevData, submission];
            })
          }
        })
      });
    }
  }, [students]);

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
