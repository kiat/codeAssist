import { CheckOutlined, CloseOutlined } from "@ant-design/icons";
import { Button, Card, Col, Form, Input, Row, Typography } from "antd";
import { useEffect, useRef } from "react";

export default ({
  order,
  point,
  text,
  editIndex,
  changeEditIndex,
  updateFormattingRecord,
  deleteFormattingRecord,
}) => {
  const cardRef = useRef();

  useEffect(() => {
    const clickCard = () => {
      changeEditIndex(order);
    };

    const ref = cardRef.current;

    ref.addEventListener("click", clickCard);

    return () => ref.removeEventListener("click", clickCard);
  }, [changeEditIndex, order]);

  return (
    <Card
      ref={cardRef}
      bodyStyle={{ height: editIndex === order ? "130px" : "100px" }}
    >
      <Form
        initialValues={{ point, text }}
        onFinish={values => {
          updateFormattingRecord(order, values);
        }}
      >
        <Row gutter={20}>
          <Col span={1}>{order + 1}</Col>
          <Col span={19}>
            {editIndex === order ? (
              <>
                <Form.Item name='point'>
                  <Input />
                </Form.Item>
                <Form.Item name='text'>
                  <Input />
                </Form.Item>
              </>
            ) : point ? (
              <>
                <Typography.Paragraph>{point}</Typography.Paragraph>
                <Typography.Paragraph>
                  {text || "Click here to replace this description."}
                </Typography.Paragraph>
              </>
            ) : (
              <Typography.Paragraph>
                Click here to replace this description.
              </Typography.Paragraph>
            )}
          </Col>
          <Col span={4}>
            {editIndex === order ? (
              <>
                <Button
                  type='text'
                  icon={<CheckOutlined />}
                  // onClick={updateFormattingRecord}
                  htmlType='submit'
                />
                <Button
                  type='text'
                  icon={<CloseOutlined />}
                  onClick={() => deleteFormattingRecord(order)}
                />
              </>
            ) : null}
          </Col>
        </Row>
      </Form>
    </Card>
  );
};
