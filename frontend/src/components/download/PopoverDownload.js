import { DownloadOutlined } from "@ant-design/icons";
import { Button, Popover, Space, Typography } from "antd";

export default () => {
  return (
    <Popover
      content={
        <Space direction='vertical' style={{ color: "black" }}>
          <Typography.Link>
            <DownloadOutlined />
            <span> Download CSV</span>
          </Typography.Link>
          <Typography.Link>
            <DownloadOutlined />
            <span> Download for Excel</span>
          </Typography.Link>
        </Space>
      }
    >
      <Button icon={<DownloadOutlined />}>Download Grades</Button>
    </Popover>
  );
};
