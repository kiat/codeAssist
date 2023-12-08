import { DeleteOutlined } from "@ant-design/icons";
import { Button, Card, Checkbox, Col, DatePicker, Form, Input, message, PageHeader, Radio, Row, Space, } from "antd";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getAssignment, updateAssignment } from "../../services/assignment";
import moment from "moment";

export default () => {
  const { assignmentId } = useParams();
  const [form] = Form.useForm();
  const [courseId, setCourseId] = useState("");
  const [publishedBefore, setPubBefore] = useState(undefined);
  const [originalPublish, setOGPub] = useState(undefined);

  const getAssignmentInfo = useCallback(() => {
    getAssignment({ assignment_id: assignmentId }).then(res => {
      const { name, published, due_date, autograder_points, course_id, published_date } = res.data || {};
      setPubBefore(published);
      setOGPub(published_date);
      setCourseId(course_id)
      form.setFieldsValue({
        name,
        published,
        autograderPoints: autograder_points,
        dueDate: moment.utc(due_date).local(),
        releaseDate: moment.utc(published_date).local()
      });
    });
  }, [assignmentId, form]);

  useEffect(() => {
    getAssignmentInfo();
  }, [getAssignmentInfo]);

  const handleDeleteAssignment = (assignmentId) => {
    if (!assignmentId) {
      console.error('Assignment ID is undefined');
      message.error('Cannot delete assignment without an ID');
      return Promise.reject(new Error('Assignment ID is undefined'));
    }

    return fetch(`${process.env.REACT_APP_API_URL}/delete_assignment?assignment_id=${assignmentId}`, {
      method: "DELETE",
      mode: 'cors',
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Network response was not ok, status: ${response.status}`);
        }
        return response.json();
      })
      .catch(error => {
        console.error('There has been a problem with the fetch operation:', error);
        message.error('Failed to delete assignment');
        return Promise.reject(error);
      });
  };


  const currentDate = () => {
    const current = new Date();
    const formatDate = current.toISOString();
    return formatDate
  }

  const finishForm = () => {
    const values = form.getFieldsValue();
    let publishedDate = undefined;
    if (values.published === true) {
      publishedDate = (publishedBefore && originalPublish) ? originalPublish : currentDate();
    } else {
      publishedDate = values.releaseDate._d;
    }

    const newAssignmentData = {
      assignment_id: assignmentId,
      name: values.name,
      course_id: courseId,
      due_date: values.dueDate._d,
      autograder_points: values.autograderPoints,
      anonymous_grading: values.submissionAnonymization,
      manual_grading: values.manualGrading,
      late_submission: values.allowLateSubmissions,
      late_due_date: values.lateDueDate,
      enable_group: values.groupSubmission,
      group_size: values.limitGroupSize,
      leaderboard: values.leaderBoard,
      published: values.published,
      published_date: publishedDate
    };
    const validData = Object.fromEntries(
      Object.entries(newAssignmentData).filter(([_, value]) => value !== undefined)
    );
    updateAssignment(validData).then(res => {
      message.success("Successfully updated assignment");
    });
  }

  const navigate = useNavigate();
  const navigateMainPage = () => {
    navigate(`/instructorDashboard/${courseId}`)
  }

  return (
    <>
      <PageHeader title='Edit Programming Assignment' />
      <Form
        layout='vertical'
        form={form}
        onFinish={() => {
          finishForm();
          navigateMainPage();
        }}
      >
        <Card bordered={false} title='Basic Settings'>
          {/* <Form.Item label='TITLE'> */}
          <Form.Item label={<span>TITLE</span>} name='name'>
            <Input />
          </Form.Item>
          <Form.Item label='PUBLISHED' name='published'>
            <Radio.Group
              options={[
                { label: "YES", value: true },
                { label: "NO", value: false },
              ]}
            />
          </Form.Item>
          <Form.Item label='SUBMISSION ANONYMIZATION'>
            <Checkbox>Enable Anonymous Grading</Checkbox>
            <div style={{ marginLeft: "24px", color: "grey" }}>
              Hide identifiable student information from being listed with
              submissions.
            </div>
          </Form.Item>
          <Form.Item label='CANVAS ASSIGNMENT'>
            <Space>
              <Input style={{ width: "205px" }} />
              <Button>Change</Button>
              <Button danger type='primary'>
                Unlink
              </Button>
            </Space>
          </Form.Item>
          <Form.Item>
            <Row gutter={20}>
              <Col>
                <Form.Item label='RELEASE DATE (CST)' name='releaseDate'>
                  <DatePicker showTime style={{ width: "100%" }} />
                </Form.Item>
                <Form.Item>
                  <Checkbox>Allow Late Submissions</Checkbox>
                </Form.Item>
              </Col>
              <Col>
                <Form.Item label='DUE DATE (CST)' name='dueDate'>
                  <DatePicker showTime style={{ width: "100%" }} />
                </Form.Item>
                <Form.Item label='LATE DUE DATE (CST)' name='lateDueDate'>
                  <DatePicker showTime style={{ width: "100%" }} />
                </Form.Item>
              </Col>
            </Row>
          </Form.Item>
          <Form.Item label='GROUP SUBMISSION'>
            <Checkbox>Enable Group Submission</Checkbox>
          </Form.Item>
          <Form.Item label='LIMIT GROUP SIZE'>
            <Input placeholder='No Max' />
          </Form.Item>
          <Form.Item label='MANUAL GRADING'>
            <Checkbox>Enable Manual Grading</Checkbox>
          </Form.Item>
          <Form.Item label='LEADERBOARD'>
            <Checkbox>Enable Leaderboard</Checkbox>
          </Form.Item>
          <Form.Item label='DEFAULT NUMBER OF ENTRIES SHOWN' name="leaderBoard">
            <Input placeholder='No Max' />
          </Form.Item>
          <Form.Item label='SUBMISSION METHODS ENABLED'>
            <Space direction='vertical'>
              <Checkbox>Upload</Checkbox>
              <Checkbox>GitHub</Checkbox>
              <Checkbox>Bitbucket</Checkbox>
            </Space>
          </Form.Item>
          <Form.Item label='IGNORED FILES'>
            <Input.TextArea />
            <span style={{ color: "grey" }}>Follows gitignore format.</span>
          </Form.Item>
        </Card>
        <Card bordered={false} title='Autograder Settings'>
          <Form.Item label='AUTOGRADER POINTS' name='autograderPoints'>
            <Input />
          </Form.Item>
          {/* <Form.Item
            label={
              <Space direction='vertical'>
                <div>CONTAINER SPECIFICATIONS</div>
                <div style={{ color: "grey" }}>
                  Your autograder will have access to at least the portion of
                  CPU allocated, and at most the memory allocated.
                </div>
              </Space>
            }
          >
            <Space direction='vertical'>
              <Checkbox>0.5 CPU, 0.75GB RAM</Checkbox>
              <Checkbox>1.0 CPU, 1.5GB RAM</Checkbox>
              <Checkbox>2.0 CPU, 3.0GB RAM</Checkbox>
              <Checkbox>4.0 CPU, 6.0GB RAM</Checkbox>
            </Space>
          </Form.Item>
          <Form.Item
            label={
              <Space direction='vertical'>
                <div>AUTOGRADER TIMEOUT</div>
                <div style={{ color: "grey" }}>
                  Your autograder will be timed out after this amount of time.
                </div>
              </Space>
            }
          >
            <Select
              options={[
                { label: "10 minutes", value: "10" },
                { label: "20 minutes", value: "20" },
              ]}
            />
          </Form.Item> */}
          <Form.Item>
            <Space>
              <Button type='primary' htmlType='submit'>
                Save
              </Button>
              <Button
                danger type='primary'
                icon={<DeleteOutlined />}
                onClick={() => {
                  handleDeleteAssignment(assignmentId)
                    .then(() => {
                      // Only navigate away if deletion was successful
                      navigateMainPage();
                    })
                    .catch((error) => {
                      message.error('Failed to delete assignment');
                    });
                }}>
                Delete assignment
              </Button>
            </Space>
          </Form.Item>
        </Card>
      </Form>
    </>
  );
};
