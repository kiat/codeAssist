import {
  Button,
  Checkbox,
  Col,
  Form,
  Modal,
  Row,
  Select,
  Space,
  Typography,
  DatePicker,
} from "antd";
import { useState } from "react";
import moment from "moment";

export default ({
  open,
  onCancel,
  students,
  assignmentInfo,
  onFinish,
  form,
}) => {
  const [checkedValues, setCheckedValues] = useState({
    releaseDate: false,
    dueDate: false,
    lateDueDate: false,
  });

  const handleCheckBoxChange = (type) => {
    setCheckedValues((prev) => ({
      ...prev,
      [type]: !prev[type],
    }));
  };
  return (
    <Modal
      open={open}
      onCancel={onCancel}
      onOk={() => form.submit()}
      title="Add an Extension"
    >
      <Form layout="vertical" form={form} onFinish={onFinish}>
        <Form.Item
          label="STUDENT"
          name="student"
          rules={[{ required: true, message: "Please select a student" }]}
        >
          <Select
            showSearch
            placeholder="Search students by name or email"
            filterOption={(input, option) =>
              option.label.toLowerCase().includes(input.toLowerCase())
            }
            options={students.map((student) => ({
              label: student.name + " - " + student.email_address,
              value: student.id,
            }))}
          />
        </Form.Item>
        <div
          style={{
            backgroundColor: "#f8f9f9",
            paddingTop: "15px",
            paddingLeft: "15px",
            marginBottom: "20px",
          }}
        >
          <Row>
            <Col span={12}>
              <div>
                <Typography.Title level={5}>
                  RELEASE DATE (CST)
                </Typography.Title>
                <Typography.Paragraph>
                  {assignmentInfo && assignmentInfo.published_date
                    ? moment(assignmentInfo.published_date).format(
                        "yyyy-MM-DD HH:mm:ss"
                      )
                    : "--"}
                </Typography.Paragraph>
              </div>
              <div>
                <Typography.Title level={5}>
                  LATE DUE DATE (CST)
                </Typography.Title>
                <Typography.Paragraph>
                  {assignmentInfo && assignmentInfo.late_due_date
                    ? moment(assignmentInfo.late_due_date).format(
                        "yyyy-MM-DD HH:mm:ss"
                      )
                    : "--"}
                </Typography.Paragraph>
              </div>
            </Col>
            <Col span={12}>
              <div>
                <Typography.Title level={5}>DUE DATE (CST)</Typography.Title>
                <Typography.Paragraph>
                  {assignmentInfo && assignmentInfo.due_date
                    ? moment(assignmentInfo.due_date).format(
                        "yyyy-MM-DD HH:mm:ss"
                      )
                    : "--"}
                </Typography.Paragraph>
              </div>
            </Col>
          </Row>
        </div>
        <Form.Item label="EXTENSION TYPE">
          <Space direction="vertical">
            <Checkbox
              checked={checkedValues.releaseDate}
              onChange={() => handleCheckBoxChange("releaseDate")}
            >
              Release Date
            </Checkbox>
            {checkedValues.releaseDate && (
              <Form.Item name="releaseDate">
                <DatePicker showTime style={{ width: "100%" }} />
              </Form.Item>
            )}
            <Checkbox
              checked={checkedValues.dueDate}
              onChange={() => handleCheckBoxChange("dueDate")}
            >
              Due Date
            </Checkbox>
            {checkedValues.dueDate && (
              <Form.Item name="dueDate">
                <DatePicker showTime style={{ width: "100%" }} />
              </Form.Item>
            )}
            <Checkbox
              checked={checkedValues.lateDueDate}
              onChange={() => handleCheckBoxChange("lateDueDate")}
            >
              Late Due Date
            </Checkbox>
            {checkedValues.lateDueDate && (
              <Form.Item name="lateDueDate">
                <DatePicker showTime style={{ width: "100%" }} />
              </Form.Item>
            )}
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};
