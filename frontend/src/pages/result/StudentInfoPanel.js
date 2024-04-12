import { Typography, Space } from "antd";

export default function StudentInfoPanel({ studentName, score, totalPoints }) {
  return (
    <Space direction="vertical" size="middle" style={{ paddingLeft: "30px", paddingTop: "20px" }}>
      <Typography.Title level={5}>STUDENT</Typography.Title>
      <Typography.Text>{studentName}</Typography.Text>
      <Typography.Title level={5}>AUTOGRADER SCORE</Typography.Title>
      <Typography.Title level={4} style={{ marginTop: "-15px", fontWeight: "700" }}>
        {score}/{totalPoints}
      </Typography.Title>
    </Space>
  );
}
