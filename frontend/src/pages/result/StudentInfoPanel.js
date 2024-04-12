import { Typography, Space} from "antd";
import { CheckCircleOutlined } from '@ant-design/icons';



export default function StudentInfoPanel({ assignmentName, studentName, score, totalPoints }) {
    return (
    <Space direction="vertical" size="middle" style={{ paddingLeft: "20px", paddingTop: "20px" }}>
     <Typography.Title level={4}>{assignmentName}</Typography.Title>
      <Space direction="horizontal" size="middle" >
        <CheckCircleOutlined style={{ color: 'green' }} />Graded
       </Space>
      <Space direction="vertical" size="middle" style={{ paddingTop: "20px" }}>
        <div>Select each question to review feedback and grading details.</div>
        <div><strong>Student</strong><br />{studentName}</div>
        <div><strong>Total Points</strong><br />{totalPoints}</div>
        <div><strong>Autograder Score</strong><br />{totalPoints}</div>
      </Space>
    </Space>
  );
}
