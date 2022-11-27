import { CloseOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  PageHeader,
  Row,
  Space,
  Typography,
} from "antd";
import { useContext, useState } from "react";
import { GlobalContext } from "../../App";

export default () => {
  const { assignmentInfo } = useContext(GlobalContext);
  const [assignmentData, setAssignmentData] = useState();

  const getAssignmentData = () => {
    setAssignmentData([
      { title: "Autograder", points: 90 },
      { title: "Formatting", points: 10 },
      { title: "asdafasfaffffs", points: 10 },
    ]);
  };

  if (!assignmentData) {
    getAssignmentData();
  }

  return (
    <>
      <PageHeader title={`Outline for ${assignmentInfo?.name}`}>
        <Typography.Paragraph>
          <span>100</span>
          <span> points total</span>
        </Typography.Paragraph>
        <Typography.Paragraph>
          Create questions and subquestions via the + buttons below. Reorder and
          indent questions by dragging them in the outline.
        </Typography.Paragraph>
      </PageHeader>
      <Card style={{ width: "760px", marginLeft: "24px" }}>
        <Form>
          <Row gutter={20}>
            <Col span={1}>
              <Form.Item>#</Form.Item>
            </Col>
            <Col span={17}>
              <Form.Item>TITLE</Form.Item>
            </Col>
            <Col span={3}>
              <Form.Item>POINTS</Form.Item>
            </Col>
            <Col span={3}></Col>
          </Row>

          <Form.List name='pointDetail' initialValue={assignmentData}>
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Row key={key} gutter={20}>
                    <Col span={1}>
                      <Form.Item {...restField}>{key + 1}</Form.Item>
                    </Col>
                    <Col span={17}>
                      <Form.Item {...restField} name={[name, "title"]}>
                        <Input disabled={key < 2 ? true : false} />
                      </Form.Item>
                    </Col>
                    <Col span={3}>
                      <Form.Item {...restField} name={[name, "points"]}>
                        <InputNumber />
                      </Form.Item>
                    </Col>
                    <Col span={3}>
                      <Button
                        type='text'
                        danger
                        icon={<CloseOutlined />}
                        onClick={() => remove(name)}
                      />
                      <Button
                        type='text'
                        icon={<PlusOutlined />}
                        onClick={add}
                      />
                    </Col>
                  </Row>
                ))}
                <Form.Item>
                  <span onClick={add}>
                    <PlusOutlined />
                    <span> new question</span>
                  </span>
                </Form.Item>
              </>
            )}
          </Form.List>
          <Form.Item>
            <Space>
              <Button type='primary'>Save outline</Button>
              <Button type='primary' danger>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </>
  );
};
