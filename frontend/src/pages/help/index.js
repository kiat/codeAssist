import { Card, PageHeader, Typography } from "antd";

export default function HelpPage() {
  return (
    <div style={{ padding: 24 }}>
      <PageHeader title="Help" />
      <Card>
        <Typography.Title level={4}>Getting started</Typography.Title>
        <Typography.Paragraph>
          Use the dashboard to view assignments, review submissions, and manage course settings.
        </Typography.Paragraph>
        <Typography.Title level={5}>Need more help?</Typography.Title>
        <Typography.Paragraph>
          Contact your course administrator or instructor for additional support.
        </Typography.Paragraph>
      </Card>
    </div>
  );
}
