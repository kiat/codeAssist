import { Card, Col, Collapse, List, Modal, Row, Typography } from "antd";
import { useState } from "react";
import { courseInfo } from "./mock";

export default ({ open, onCancel }) => {
  const [questions, setQuestions] = useState([]);
  const [assignmentSelected, setAssignmentSelected] = useState("");
  const [questionsSelected, setQuestionsSelected] = useState("");
  const [rubric, setRubric] = useState([]);

  return (
    <Modal
      title='Import Rubric'
      open={open}
      width={900}
      bodyStyle={{
        height: "500px",
      }}
      onCancel={onCancel}
    >
      <Row gutter={20}>
        <Col span={8}>
          <Card
            title='ASSIGNMENT'
            size='small'
            bordered={false}
            // bodyStyle={{ overflow: "auto", height: "438px" }}
          >
            <div
              className='content'
              style={{ overflow: "auto", height: "438px" }}
            >
              <Collapse bordered={false}>
                {courseInfo.map((item, index) => (
                  <Collapse.Panel header={item.course.name} key={index}>
                    <List
                      dataSource={item.assignments}
                      renderItem={item2 => (
                        <List.Item
                          style={{
                            backgroundColor:
                              assignmentSelected === item2.id ? "#a5d2fc" : "",
                          }}
                          onClick={() => {
                            setAssignmentSelected(item2.id);
                            setQuestions(item2.questions);
                          }}
                        >
                          <Typography.Text>{item2.assignment}</Typography.Text>
                        </List.Item>
                      )}
                    />
                  </Collapse.Panel>
                ))}
              </Collapse>
            </div>
          </Card>
        </Col>
        <Col span={8}>
          <Card
            title='QUESTION'
            size='small'
            bordered={false}
            bodyStyle={{ overflow: "auto", height: "438px" }}
          >
            <List
              // bordered
              dataSource={questions}
              renderItem={item => (
                <List.Item
                  style={{
                    backgroundColor:
                      questionsSelected === item.id ? "#a5d2fc" : "",
                  }}
                  onClick={() => {
                    setQuestionsSelected(item.id);
                    setRubric(item.rubric);
                  }}
                >
                  <Typography.Text>{item.question}</Typography.Text>
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card
            title='RUBRIC PREVIEW'
            size='small'
            bordered={false}
            bodyStyle={{ overflow: "auto", height: "438px" }}
          >
            <List
              // bordered
              dataSource={rubric}
              renderItem={item => (
                <List.Item>
                  <div>
                    <div>
                      <Typography.Text>{item.point}</Typography.Text>
                    </div>
                    <div>
                      <Typography.Text>{item.description}</Typography.Text>
                    </div>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </Modal>
  );
};
