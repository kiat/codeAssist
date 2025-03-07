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
  message,
  Popconfirm,
} from "antd";
import { useEffect, useState, useCallback } from "react";
import { useContext } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { GlobalContext } from "../../../App";
import { getCourseAssignments, updateCourse , deleteCourse, deleteAllAssignments, getCourseInfo} from "../../../services/course";

export default () => {
  const { courseId } = useParams();
  const [assignments, setAssignments] = useState([]);

  // Used to manage form state
  const [form] = Form.useForm();

  const { courseInfo, updateCourseInfo } = useContext(GlobalContext);


  useEffect(() => {
    fetchCourseData();
  }, []);

  const fetchCourseData = async () => {
    try {
      const res = await getCourseInfo({course_id: courseId});
      form.setFieldsValue(res.data[0]);
    }
    catch(error) {
      console.error("Error fetching course data: ", error)
    }
  };

  const getAssignments = useCallback(() => {
    getCourseAssignments({ course_id: courseId }).then((res) => {
      setAssignments(res.data);
    });
  }, [courseId]);

  useEffect(() => {
    getAssignments();
  }, [getAssignments]);

  const navigate = useNavigate();

  const handleDeleteAllAssignments = async (courseId) => {
    try {
      await deleteAllAssignments({"course_id": courseId});
      message.success("All assignments deleted successfully");
    }
    catch(error) {
      console.error("Error deleting all assignments: ", error);
    }
  };

  const handleDeleteCourse = async (courseId) => {
    try {
      await deleteCourse({"course_id" : courseId});
      message.success("Course deleted successfully");
      navigateHome();
    }
    catch (error) {
      console.error("Error deleting course:", error);
    }
  };

  const navigateHome = () => {
    navigate("/dashboard");
  };

  const navigateMainPage = () => {
    navigate(`/instructorDashboard/${courseId}`);
  };

  const onFinish = async (values) => {
    const dataToSend = {
      course_id: courseId,
      ...Object.fromEntries(
        Object.entries(values).filter(([_, value]) => value !== undefined)
      ),
    };

    try {
      await updateCourse(dataToSend);
      message.success("Course updated successfully");

      const res = await getCourseInfo({course_id: courseId});
      updateCourseInfo(res.data[0]);

      navigateMainPage();
    } catch (error)  {
      console.error("Error updating course:", error);
    }
  };

  return (
    <Form
      form={form} 
      onFinish={onFinish}
      layout="vertical"
      wrapperCol={{
        lg: 12,
      }}
      style={{
        marginLeft: "20px",
      }}
    >
      <Space direction="vertical" style={{ width: "100%" }}>
        <PageHeader title="Edit Course" />
        <Card
          title="Basic Settings"
          bodyStyle={{
            width: "100%",
          }}
        >
          <Form.Item label="ENTRY CODE" name="entryCode">
            <Input />
          </Form.Item>
          <Form.Item label="ALLOW ENTRY CODE" wrapperCol={24} name="allowEntryCode" valuePropName="checked" >
            <Checkbox            >
              Allow students to enroll via course entry code
            </Checkbox>
          </Form.Item>
          <Form.Item label="COURSE NAME" name="name">
            <Input />
          </Form.Item>
          <Form.Item label="COURSE DESCRIPTION" name="description">
            <Input.TextArea />
          </Form.Item>
          <Form.Item>
            <Row gutter={20}>
              <Col span={12}>
                <Form.Item label="SEMESTER" name="semester" wrapperCol={24}>
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
                <Form.Item label="YEAR" name="year" wrapperCol={24}>
                  <Input />
                </Form.Item>
              </Col>
            </Row>
          </Form.Item>
        </Card>
        {/* <Card title="Grading Defaults">
          <p>
            Any newly created assignments will have these settings. Existing
            assignments won't be changed.
          </p>
          <Form.Item label="DEFAULT SCORING METHOD" name="defaultScoringMethod">
            <Radio.Group
              options={[
                { label: "Negative Scoring", value: 0 },
                { label: "Positive Scoring", value: 1 },
              ]}
              value={formData.defaultScoringMethod}
            />
          </Form.Item>
          <Form.Item
            label="DEFAULT SCORE BOUNDS"
            name="DefaultScoreBounds"
            wrapperCol={24}
          >
            <Checkbox.Group value={formData.DefaultScoreBounds}>
              <Space direction="vertical">
                <Checkbox value="ceiling">
                  Ceiling (maximum score is determined by the Assignment
                  Outline)
                </Checkbox>
                <Checkbox value="floor">Floor (minimum score is 0.0)</Checkbox>
              </Space>
            </Checkbox.Group>
          </Form.Item>
        </Card> */}
        <Card title="Modify Course">
          <Typography.Title level={5}>COURSE ACTIONS</Typography.Title>
          <Space>
            <Button
              type="primary"
              htmlType="submit"
            >
              Update Course
            </Button>
            <Button type="primary">Deactivate</Button>
            <Button type="primary">Reactivate</Button>
          </Space>
          <Typography.Title level={5} style={{ marginTop: "10px" }}>
            DANGER ZONE
          </Typography.Title>
          <Space>
            <Popconfirm
              title="Are you sure you want to delete this course?"
              onConfirm={() => {
                handleDeleteCourse(courseId)
              }}
              okText="Yes"
              cancelText="No"
            >
              <Button danger type="primary" icon={<DeleteOutlined />}>
                Delete Course
              </Button>
            </Popconfirm>
            <Popconfirm
              title="Are you sure you want to delete all assignments?"
              onConfirm={() => {
                handleDeleteAllAssignments(courseId)
              }}
              okText="Yes"
              cancelText="No"
            >
              <Button danger type="primary" icon={<DeleteOutlined />}>
                Delete All Assignments
              </Button>
            </Popconfirm>
          </Space>
        </Card>
      </Space>
    </Form>
  );
};
