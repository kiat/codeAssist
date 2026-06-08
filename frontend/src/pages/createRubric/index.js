import {
  DownloadOutlined,
  PlusOutlined,
  RightOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { Button, Card, PageHeader, Space, Typography } from "antd";
import { useCallback, useState } from "react";
import PageBottom from "../../components/layout/pageBottom";
import PageContent from "../../components/layout/pageContent";
import FormattingCard from "./FormattingCard";
import ImportRubricJsModal from "./ImportRubric.jsModal";
import RubricOptions from "./RubricOptions";

const data = [
  {
    point: "-0.0",
    text: "Correct",
    // order: 1,
  },
  {
    point: "-1.0",
    text: "Missing header comment",
    // order: 2,
  },
  {
    point: "-1.0",
    text: "",
    // order: 3,
  },
  {
    point: "",
    text: "sdgsagdfffffffffffffffdg",
    // order: 4,
  },
  {
    // order: 5,
    point: "",
    text: "",
  },
];

export default () => {
  const [editIndex, setEditIndex] = useState("");
  const [formattingData, setFormattingData] = useState(data);
  const [rubricOptionsOpen, setRubricOptionsOpen] = useState(false);
  const [importRubricOpen, setImportRubricOpen] = useState(false);

  const toggleRubricOptionsOpen = useCallback(() => {
    setRubricOptionsOpen(t => !t);
  }, []);

  const toggleImportRubricOpen = useCallback(() => {
    setImportRubricOpen(t => !t);
  }, []);

  const changeEditIndex = useCallback(value => {
    setEditIndex(value);
  }, []);

  const updateFormattingRecord = useCallback(
    (index, value) => {
      // const temp = formattingData
      formattingData.splice(index, 1, value);
      setFormattingData(formattingData);
      setEditIndex("");
    },
    [formattingData]
  );

  const deleteFormattingRecord = useCallback(
    index => {
      formattingData.splice(index, 1);
      setFormattingData(formattingData);
      setEditIndex("");
    },
    [formattingData]
  );

  return (
    <>
      <PageContent>
        <PageHeader title='Create Rubric'>
          <Typography.Paragraph>10 points</Typography.Paragraph>
        </PageHeader>
        {/* <Divider /> */}
        <Card
          extra={
            <Button
              type='text'
              icon={<SettingOutlined />}
              onClick={toggleRubricOptionsOpen}
            >
              Rubric Settings
            </Button>
          }
          title={
            <>
              <div>Q2 formatting</div>
              <span style={{ fontWeight: "normal", fontSize: "12px" }}>
                10.0 points
              </span>
            </>
          }
        >
          <Space direction='vertical' style={{ width: "600px" }}>
            {formattingData.map((item, index) => (
              <FormattingCard
                key={index}
                order={index}
                point={item?.point}
                text={item?.text}
                editIndex={editIndex}
                changeEditIndex={changeEditIndex}
                updateFormattingRecord={updateFormattingRecord}
                deleteFormattingRecord={deleteFormattingRecord}
              />
            ))}
            <div>
              <Space>
                <Button
                  size='large'
                  icon={<PlusOutlined />}
                  // onClick={addFormattingRecord}
                  onClick={() => {
                    // // formattingData.push({ point: "", text: "" });
                    // formattingData.splice(formattingData.length, 0, {
                    //   point: "",
                    //   text: "",
                    // });
                    // setFormattingData(formattingData);
                    setFormattingData(
                      formattingData.concat({ point: "", text: "" })
                    );
                  }}
                >
                  Add Rubric Item
                </Button>
                <Button
                  size='large'
                  icon={<DownloadOutlined />}
                  onClick={toggleImportRubricOpen}
                >
                  Import Rubric
                </Button>
              </Space>
            </div>
          </Space>
        </Card>
      </PageContent>
      <PageBottom>
        <Button>
          <span>Manage Submissions</span>
          <RightOutlined />
        </Button>
      </PageBottom>
      <RubricOptions
        open={rubricOptionsOpen}
        onCancel={toggleRubricOptionsOpen}
      />
      <ImportRubricJsModal
        open={importRubricOpen}
        onCancel={toggleImportRubricOpen}
      />
    </>
  );
};
