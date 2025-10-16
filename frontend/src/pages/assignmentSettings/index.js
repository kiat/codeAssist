import { DeleteOutlined } from "@ant-design/icons";
import { 
  Button, 
  Card, 
  Checkbox, 
  Col, 
  DatePicker, 
  Form, 
  Input, 
  message, 
  PageHeader, 
  Radio, 
  Row, 
  Space,
  Popconfirm
} from "antd";
import { useCallback, useEffect, useState } from "react";
import { useContext } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { GlobalContext } from "../../App";
import { deleteAssignment, deleteSubmissions, getAssignment, updateAssignment } from "../../services/assignment";
import moment from "moment";

export default () => {
  const { assignmentId } = useParams();
  const [form] = Form.useForm();
  const [courseId, setCourseId] = useState("");
  const [publishedBefore, setPubBefore] = useState(undefined);
  const [originalPublish, setOGPub] = useState(undefined);
  const [enableAiFeedback, setEnableAiFeedback] = useState(false);
  const { assignmentInfo, updateAssignmentInfo } = useContext(GlobalContext);


  const getAssignmentInfo = useCallback(() => {
    getAssignment({ assignment_id: assignmentId }).then(res => {
      const { name, published, due_date, autograder_points, course_id, published_date, 
        ai_feedback_enabled, ai_feedback_prompt, ai_feedback_model, ai_feedback_temperature } = res.data || {};      
        setPubBefore(published);

      setOGPub(published_date);
      setCourseId(course_id)
      form.setFieldsValue({
        name,
        published,
        autograderPoints: autograder_points,
        dueDate: moment.utc(due_date).local(),
        releaseDate: moment.utc(published_date).local(),
        enableAiFeedback: ai_feedback_enabled,
        ai_feedback_prompt,
        ai_feedback_model,
        ai_feedback_temperature
      });

      setEnableAiFeedback(ai_feedback_enabled);
    });
  }, [assignmentId, form]);

  useEffect(() => {
    getAssignmentInfo();
  }, [getAssignmentInfo]);

  const handleDeleteAssignment = async (assignmentId) => {
  if (!assignmentId) {
    message.error('Assignment ID is undefined');
    return;
  }
  try {
    await deleteAssignment(assignmentId);
    message.success("Assignment deleted successfully");
  } catch (error) {
    console.error("Failed to delete assignment:", error);
    message.error("Failed to delete assignment");
  }
};

const handleDeleteSubmissions = async (assignmentId) => {
  if (!assignmentId) {
    message.error('Assignment ID is undefined');
    return;
  }
  try {
    await deleteSubmissions(assignmentId);
    message.success("All submissions deleted successfully");
  } catch (error) {
    console.error("Failed to delete submissions:", error);
    message.error("Failed to delete submissions");
  }
};

  const currentDate = () => {
    const current = new Date();
    const formatDate = current.toISOString();
    return formatDate
  }

  const finishForm = async () => {
      if (!assignmentId) {
      message.error("Assignment ID is missing. Cannot update.");
      return;
    }

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
      published_date: publishedDate,

      // AI Feedback Config
      ai_feedback_enabled: values.enableAiFeedback,
      ai_feedback_prompt: values.ai_feedback_prompt,
      ai_feedback_model: values.ai_feedback_model,
      ai_feedback_temperature: values.ai_feedback_temperature
    };
    const validData = Object.fromEntries(
      Object.entries(newAssignmentData).filter(([_, value]) => value !== undefined)
    );
    try {
    await updateAssignment(validData);
    message.success("Successfully updated assignment");

    const res = await getAssignment({ assignment_id: assignmentId });
    updateAssignmentInfo(res.data);

  } catch (err) {
    message.error("Failed to update assignment. Please try again.");
    console.error("Update error:", err);
  }
};

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
        <Card >
          {/* <Form.Item label='TITLE'> */}
          <Form.Item 
            label={<span>NAME</span>} 
            name='name' 
            rules={[{ required: true, message: 'Please enter a title' }]}>
            <Input />
          </Form.Item>
          <Form.Item 
            label='AUTOGRADER POINTS' 
            name='autograderPoints' 
            rules={[{ required: true, message: 'Please enter points' }]}>
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
          {/* NEED TO CONNECT TO BACKEND  */}
          {/* <Form.Item label='SUBMISSION ANONYMIZATION'>
            <Checkbox>Enable Anonymous Grading</Checkbox>
            <div style={{ marginLeft: "24px", color: "grey" }}>
              Hide identifiable student information from being listed with
              submissions.
            </div>
          </Form.Item> */} 
          {/* <Form.Item label='CANVAS ASSIGNMENT'>
            <Space>
              <Input style={{ width: "205px" }} />
              <Button>Change</Button>
              <Button danger type='primary'>
                Unlink
              </Button>
            </Space>
          </Form.Item> */}
          <Form.Item>
            <Row gutter={20}>
              <Col>
                <Form.Item
                  label='RELEASE DATE (CST)'
                  name='releaseDate'
                  rules={[{ required: true, message: 'Please select a release date' }]}
                >
                  <DatePicker showTime style={{ width: "100%" }} />
                </Form.Item>
                <Form.Item>
                  <Checkbox>Allow Late Submissions</Checkbox>
                </Form.Item>
              </Col>
              <Col>
                <Form.Item
                  label='DUE DATE (CST)'
                  name='dueDate'
                  rules={[{ required: true, message: 'Please select a due date' }]}
                >
                  <DatePicker showTime style={{ width: "100%" }} />
                </Form.Item>
                <Form.Item label='LATE DUE DATE (CST)' name='lateDueDate'>
                  <DatePicker showTime style={{ width: "100%" }} />
                </Form.Item>
              </Col>
            </Row>
          </Form.Item>
          {/* <Form.Item label='GROUP SUBMISSION'>
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
          </Form.Item> */}
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

        {/* AI Settings */}
        <Form.Item label="ENABLE AI FEEDBACK" name="enableAiFeedback" valuePropName="checked">
          <Checkbox onChange={(e) => setEnableAiFeedback(e.target.checked)}>
            Enable AI Feedback
          </Checkbox>
        </Form.Item>

        <Form.Item
          label="AI FEEDBACK PROMPT"
          name="ai_feedback_prompt"
          rules={[{ required: enableAiFeedback, message: "Please enter a feedback prompt" }]}
        >
          <Input.TextArea
            placeholder="Enter the feedback prompt for AI"
            autoSize={{ minRows: 4, maxRows: 8 }}
            disabled={!enableAiFeedback}
          />
        </Form.Item>

        <Form.Item
          label="AI MODEL USED"
          name="ai_feedback_model"
          rules={[{ required: enableAiFeedback, message: "Please select an AI model (e.g. gpt-5o)" }]}
        >
          <Input.TextArea
            placeholder="gpt-5o"
            autoSize={{ minRows: 1, maxRows: 1}}
            disabled={!enableAiFeedback}
          />
        </Form.Item>

        {/* <Form.Item
          label="AI MODEL USED"
          name="ai_feedback_model"
          rules={[{ required: enableAiFeedback, message: "Please select an AI model" }]}
        >
          <Radio.Group disabled={!enableAiFeedback}>
            <Space direction="vertical">
              <Radio value="gpt-3.5-turbo">GPT-3.5 Turbo</Radio>
              <Radio value="gpt-4o">GPT-4o</Radio>
              <Radio value="custom-model">Custom Model</Radio>
            </Space>
          </Radio.Group>
        </Form.Item> */}

        <Form.Item
          label="MODEL TEMPERATURE"
          name="ai_feedback_temperature"
          rules={[
            { required: enableAiFeedback, message: "Please enter a temperature" },
            { pattern: /^0(\.\d+)?|1$/, message: "Enter a value between 0 and 1" }
          ]}
        >
          <Input placeholder="Enter temperature (0 to 1)" disabled={!enableAiFeedback} />
        </Form.Item>


          <Form.Item>
            <Space>
              <Button type='primary' htmlType='submit'>
                Save
              </Button>
              <Popconfirm
                title="Are you sure you want to delete this assignment?"
                onConfirm={() => handleDeleteAssignment(assignmentId).then(navigateMainPage)}
                okText="Yes"
                cancelText="No">
                <Button 
                  danger type='primary' 
                  icon={<DeleteOutlined />} >
                  Delete Assignment
                </Button>
              </Popconfirm>
              <Popconfirm
                title="Are you sure you want to delete all submissions?"
                onConfirm={() => {
                  handleDeleteSubmissions(assignmentId)
                }}
                okText="Yes"
                cancelText="No">
                <Button 
                  danger type='primary' 
                  icon={<DeleteOutlined />} >
                  Delete All Submissions
                </Button>
              </Popconfirm>
            </Space>
          </Form.Item>
        </Card>
      </Form>
    </>
  );
};