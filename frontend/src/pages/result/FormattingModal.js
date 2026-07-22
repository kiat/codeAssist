import {
  Card,
  Form,
  Input,
  Modal,
  Progress,
  Select,
  Table,
  Typography,
} from "antd";

const formattingColumns = [
  { title: "points", dataIndex: "points" },
  { title: "description", dataIndex: "description" },
];

export default ({
  open,
  onCancel,
  formattingData,
  formattingSelected,
  formattingSelectedUpdate,
}) => {
  return (
    <Modal
      open={open}
      onCancel={onCancel}
      onOk={onCancel}
      title={<Typography.Title level={3}>2: formatting</Typography.Title>}
      bodyStyle={{
        height: "calc(100vh - 400px)",
        overflow: "auto",
      }}
    >
      <Progress percent={100} showInfo={false} />
      <Typography.Paragraph>36 OF 36 GRADED</Typography.Paragraph>
      <Typography.Title level={5}>TOTAL POINTS</Typography.Title>
      <Typography.Title level={4} style={{ marginTop: 0 }}>
        10.0/10.0 pts
      </Typography.Title>
      {/* {formattingData.map((item, index) => (
        <FormattingCard
          key={index}
          order={index}
          point={item?.points}
          text={item?.description}
          editIndex={""}
          changeEditIndex={""}
          updateFormattingRecord={""}
          deleteFormattingRecord={""}
          // editIndex={editIndex}
          // changeEditIndex={changeEditIndex}
          // updateFormattingRecord={updateFormattingRecord}
          // deleteFormattingRecord={deleteFormattingRecord}
        />
      ))} */}
      <Table
        rowKey='id'
        columns={formattingColumns}
        dataSource={formattingData}
        size='small'
        showHeader={false}
        rowSelection={{
          selectedRowKeys: formattingSelected,
          onChange: formattingSelectedUpdate,
        }}
        pagination={false}
      />
      <Card>
        {/* <Space style={{ marginTop: "10px", marginBottom: "10px" }}>
          <Button
            // size='large'
            icon={<PlusOutlined />}
            onClick={() => {
              // setFormattingData(formattingData.concat({ point: "", text: "" }));
            }}
          >
            Add Rubric Item
          </Button>
          <Button
            // size='large'
            icon={<DownloadOutlined />}
            // onClick={toggleImportRubricOpen}
          >
            Import Rubric
          </Button>
        </Space> */}
        <Typography.Title level={5}>
          SUBMISSION SPECIFIC ADJUSTMENTS
        </Typography.Title>
        {/* <Card bordered={false} title='SUBMISSION SPECIFIC ADJUSTMENTS'></Card> */}
        <Form layout='vertical'>
          <Form.Item label='Point Adjustment'>
            <Input />
          </Form.Item>
          <Form.Item>
            <Input.TextArea placeholder='Provide comments specific to this submission' />
          </Form.Item>
          <Form.Item label='APPLY PREVIOUSLY USED COMMENTS'>
            <Select />
          </Form.Item>
        </Form>
      </Card>
    </Modal>
  );
};
