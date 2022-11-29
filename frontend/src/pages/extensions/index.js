import { PlusOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Input,
  PageHeader,
  Space,
  Table,
  Typography,
} from "antd";
import { useCallback } from "react";
import { useState } from "react";
import PageBottom from "../../components/layout/pageBottom";
import PageContent from "../../components/layout/pageContent";
import ExtensionModal from "./ExtensionModal";

export default () => {
  const [extensionModalOpen, setExtensionModalOpen] = useState(false);

  const toggleExtensionModalOpen = useCallback(() => {
    setExtensionModalOpen(t => !t);
  }, []);

  const columns = [
    { title: "FIRST & LAST NAME", dataIndex: "" },
    { title: "EXTENSION TYPE", dataIndex: "" },
    { title: "RELEASE (CST)", dataIndex: "" },
    { title: "DUE (CST)", dataIndex: "" },
    { title: "LATE DUE (CST)", dataIndex: "" },
    { title: "EDIT", dataIndex: "" },
  ];
  return (
    <>
      <PageContent>
        <PageHeader title='Extensions' />
        <Card title='Assignsment Settings' bordered={false}>
          <Space size='large'>
            <div>
              <Typography.Title level={5}>RELEASE DATE (CST)</Typography.Title>
              <p>Jun 26 2022 06:00 AM</p>
            </div>
            <div>
              <Typography.Title level={5}>DUE DATE (CST)</Typography.Title>
              <p>Jun 26 2022 06:00 AM</p>
            </div>
            <div>
              <Typography.Title level={5}>LATE DATE (CST)</Typography.Title>
              <p>--</p>
            </div>
          </Space>
        </Card>
        <Card bordered={false} bodyStyle={{ paddingTop: 0 }}>
          <Space direction='vertical' style={{ width: "100%" }}>
            <Input.Search
              enterButton
              placeholder='Find a student'
              style={{ width: "300px" }}
            />
            <Table
              rowKey='id'
              columns={columns}
              dataSource={[]}
              locale={{
                emptyText: (
                  <div style={{ marginTop: "50px", marginBottom: "50px" }}>
                    <Typography.Title level={4}>
                      There are no assignment extension.
                    </Typography.Title>
                    <Typography.Paragraph>
                      Add an extension for a student below.
                    </Typography.Paragraph>
                    <Button
                      type='primary'
                      ghost
                      shape='round'
                      onClick={toggleExtensionModalOpen}
                    >
                      Add an extension
                    </Button>
                  </div>
                ),
              }}
            />
          </Space>
        </Card>
      </PageContent>
      <PageBottom>
        <Button onClick={toggleExtensionModalOpen}>
          <span>Add an extension</span>
          <PlusOutlined />
        </Button>
      </PageBottom>
      <ExtensionModal
        open={extensionModalOpen}
        onCancel={toggleExtensionModalOpen}
      />
    </>
  );
};
