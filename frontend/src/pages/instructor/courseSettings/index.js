import { DeleteOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Checkbox,
  Col,
  Form,
  Input,
  PageHeader,
  Popover,
  Radio,
  Row,
  Select,
  Space,
  Typography,
} from "antd";
import { useEffect } from "react";
import { useContext } from "react";
import { useParams } from "react-router-dom";
import { GlobalContext } from "../../../App";

export default () => {
  const { courseId } = useParams();
  const { updateCourseInfo, courseInfo } = useContext(GlobalContext);

  useEffect(() => {
    if (!courseInfo.id) {
      updateCourseInfo({ id: courseId });
    }
  }, [courseId, courseInfo.id, updateCourseInfo]);

  return (
    <Form
      layout='vertical'
      wrapperCol={{
        lg: 12,
      }}
      style={{
        marginLeft: "20px",
      }}
    >
      <Space direction='vertical' style={{ width: "100%" }}>
        <PageHeader title='Edit Course' />
        <Card
          title='Basic Settings'
          // bordered={false}
          bodyStyle={{
            width: "100%",
          }}
        >
          <Form.Item label='ENTRY CODE' name='entryCode'>
            <Input />
          </Form.Item>
          <Form.Item
            label='ALLOW ENTRY CODE'
            name='allowEntryCode'
            wrapperCol={24}
          >
            <Checkbox>Allow students to enroll via course entry code</Checkbox>
          </Form.Item>
          <Form.Item label='COURSE NAME' name='courseName'>
            <Input />
          </Form.Item>
          <Form.Item label='COURSE DESCRIPTION' name='courseDescription'>
            <Input.TextArea />
          </Form.Item>
          {/* <Space>
            <Form.Item label='TERM' name='term' wrapperCol={24}>
              <Select
                options={[
                  { value: "Spring" },
                  { value: "Summer" },
                  { value: "Autumn" },
                  { value: "Winter" },
                ]}
              />
            </Form.Item>
            <Form.Item label='YEAR' name='year' wrapperCol={24}>
              <Select
                options={[
                  { value: 2022 },
                  { value: 2021 },
                  { value: 2020 },
                  { value: 2019 },
                ]}
              />
            </Form.Item>
          </Space> */}
          <Form.Item>
            <Row gutter={20}>
              <Col span={12}>
                <Form.Item label='SEMESTER' name='semester' wrapperCol={24}>
                  <Select
                    options={[
                      { value: "Spring" },
                      { value: "Summer" },
                      { value: "Fall" },
                      { value: "Winter" },
                    ]}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label='YEAR' name='year' wrapperCol={24}>
                  <Input />
                  {/* <Select
                    options={[
                      { value: 2022 },
                      { value: 2021 },
                      { value: 2020 },
                      { value: 2019 },
                    ]}
                  /> */}
                </Form.Item>
              </Col>
            </Row>
          </Form.Item>
        </Card>
        <Card
          title='Grading Defaults'
          // bordered={false}
        >
          <p>
            Any newly created assignments will have these settings. Existing
            assignments won't be changed.
          </p>
          <Form.Item label='DEFAULT SCORING METHOD' name='defaultScoringMethod'>
            <Radio.Group
              options={[
                { label: "Negative Scoring", value: 0 },
                { label: "Positive Scoring", value: 1 },
              ]}
            />
          </Form.Item>
          <Form.Item
            label='DEFAULT SCORE BOUNDS'
            name='DefaultScoreBounds'
            wrapperCol={24}
          >
            <Checkbox.Group>
              <Space direction='vertical'>
                <Checkbox value='ceiling'>
                  Ceiling (maximum score is determined by the Assignment
                  Outline)
                </Checkbox>
                <Checkbox value='floor'>Floor (minimum score is 0.0)</Checkbox>
              </Space>
            </Checkbox.Group>
          </Form.Item>
        </Card>
        <Card
          title='Modify Course'
          // bordered={false}
        >
          <Typography.Title level={5}>COURSE ACTIONS</Typography.Title>
          <Space>
            <Button type='primary'>Update Course</Button>
            <Popover
              // title='sf'
              trigger='click'
              content={
                <div style={{ width: "300px" }}>
                  This course cannot be deelted, as it contains assignments.
                  Delete the assignments and try again.
                </div>
              }
            >
              <Button type='primary' icon={<DeleteOutlined />} danger>
                Delete Course
              </Button>
            </Popover>
            <Button type='primary'>Deactivate</Button>
            <Button type='primary'>Reactivate</Button>
          </Space>
        </Card>
      </Space>
    </Form>
  );
};
