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
  Popconfirm
} from "antd";
import { useEffect, useState, useCallback } from "react";
import { useContext } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { GlobalContext } from "../../../App";
import { getCourseAssignments } from "../../../services/course";

export default () => {
  const { courseId } = useParams();
  const { updateCourseInfo, courseInfo } = useContext(GlobalContext);
  const [assignments, setAssignments] = useState([]);
  const [formData, setFormData] = useState({});
  const [placeholders, setPlaceholders] = useState({});

  useEffect(() => {
    if (!courseInfo.id) {
      updateCourseInfo({ id: courseId });
    }
    fetchCourseData(courseId);
  }, [courseId, courseInfo.id, updateCourseInfo]);

  const fetchCourseData = async (id) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/get_course_info?course_id=${id}`);
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const data = await response.json();
      setFormData(data[0]);
      setPlaceholders(data[0]);
    } catch (error) {
      console.error("Error fetching course data:", error);
    }
  };

  const getAssignments = useCallback(() => {
    getCourseAssignments({ course_id: courseId }).then(res => {
      setAssignments(res.data);
    });
  }, [courseId]);

  useEffect(() => {
    getAssignments();
  }, [getAssignments]);

  const navigate = useNavigate();

  const handleDeleteAllAssignments = (courseId) => {
    if (!courseId) {
      console.error('Course ID is undefined');
      message.error('Cannot delete assignments without an ID');
      return Promise.reject(new Error('Course ID is undefined'));
    }
  };

    return fetch(`${process.env.REACT_APP_API_URL}/delete_all_assignments?course_id=${courseId}`, {
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
        message.error('Failed to delete assignments');
        return Promise.reject(error);
      });
  };
  
  const handleDeleteCourse = (courseId) => {
    if (!courseId) {
      console.error('Course ID is undefined');
      message.error('Cannot delete course without an ID');
      return Promise.reject(new Error('Course ID is undefined'));
    }

    return fetch(`${process.env.REACT_APP_API_URL}/delete_course?course_id=${courseId}`, {
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
        message.error('Failed to delete course');
        return Promise.reject(error);
      });
  };
  
  const navigateHome = () => {
    navigate("/dashboard");
  };

  const navigateMainPage = () => {
    navigate(`/instructorDashboard/${courseId}`);
  };

  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    setFormData((prevFormData) => ({
      ...prevFormData,
      [name]: checked
    }));
  };

  const onFinish = () => {
    const dataToSend = {
      course_id: courseId,
      ...Object.fromEntries(
      Object.entries(formData).filter(([_, value]) => value !== undefined))
    };
    fetch(process.env.REACT_APP_API_URL + "/update_course", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(dataToSend),
    })
    .then((response) => {response.json()})
    .then((data) => {console.log(data)})
    .catch((error) => {console.log(error)})
  };

  return (
    <Form
      layout='vertical'
      wrapperCol={{
        lg: 12,
      }}
      style={{
        marginLeft: "20px",
      }}
      initialValues={formData}
      onValuesChange={(changedValues, allValues) => {
        setFormData(allValues);
      }}
    >
      <Space direction='vertical' style={{ width: "100%" }}>
        <PageHeader title='Edit Course' />
        <Card
          title='Basic Settings'
          bodyStyle={{
            width: "100%",
          }}
        >
          <Form.Item label='ENTRY CODE' name="entryCode">
            <Input placeholder={placeholders.entryCode || "Enter Entry Code"} />
          </Form.Item>
          <Form.Item
            label='ALLOW ENTRY CODE'
            wrapperCol={24}
          >
            <Checkbox name="allowEntryCode" checked={formData.allowEntryCode} onChange={handleCheckboxChange}>
              Allow students to enroll via course entry code
            </Checkbox>
          </Form.Item>
          <Form.Item label='COURSE NAME' name='name'>
            <Input placeholder={placeholders.name || "Enter Course Name"} />
          </Form.Item>
          <Form.Item label='COURSE DESCRIPTION' name='description'>
            <Input.TextArea placeholder={placeholders.description || "Enter Course Description"} />
          </Form.Item>
          <Form.Item>
            <Row gutter={20}>
              <Col span={12}>
                <Form.Item label='SEMESTER' name='semester' wrapperCol={24}>
                  <Select placeholder={placeholders.semester || "Select Semester"}
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
                  <Input placeholder={placeholders.year || "Enter Year"} />
                </Form.Item>
              </Col>
            </Row>
          </Form.Item>
        </Card>
        <Card
          title='Grading Defaults'
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
              value={formData.defaultScoringMethod}
            />
          </Form.Item>
          <Form.Item
            label='DEFAULT SCORE BOUNDS'
            name='DefaultScoreBounds'
            wrapperCol={24}
          >
            <Checkbox.Group value={formData.DefaultScoreBounds}>
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
        >
          <Typography.Title level={5}>COURSE ACTIONS</Typography.Title>
          <Space>
            <Button 
            type='primary' 
            onClick = {() => {
              onFinish();
              navigateMainPage();
            }}>Update Course</Button>
            <Popover
              trigger='click'
              content={
                assignments.length !== 0 && (
                  <div style={{ width: "300px" }}>
                    This course cannot be deleted, as it contains assignments.
                    Delete the assignments and try again.
                  </div>
                )
              }
            >
              <Button 
              type='primary' 
              icon={<DeleteOutlined />} 
              danger 
              onClick = {() => {
                handleDeleteCourse();
                navigateHome();
              }}>
                Delete Course
              </Button>
            </Popover>
            <Button type='primary'>Deactivate</Button>
            <Button type='primary'>Reactivate</Button>
          </Space>
          <Typography.Title level={5} style={{ marginTop: '10px' }}>DANGER ZONE</Typography.Title>
          <Space>
          <Popconfirm
            title="Are you sure you want to delete this course?"
            onConfirm={() => {
              handleDeleteCourse(courseId)
                .then(() => {
                  message.success("Course deleted");
                  // Only navigate away if deletion was successful
                  navigateHome();
                })
                .catch((error) => {
                  if (error.response && error.response.status === 410) {
                    message.error('Assignments must be deleted first');
                  } else {
                    message.error('Failed to delete course');
                  }
                });
            }}
            okText="Yes"
            cancelText="No">
            <Button 
              danger type='primary' 
              icon={<DeleteOutlined />} >
              Delete Course
            </Button>
          </Popconfirm>
          <Popconfirm
            title="Are you sure you want to delete all assignments?"
            onConfirm={() => {
              handleDeleteAllAssignments(courseId)
                .then(() => {
                  message.success("All assignments deleted");
                })
                .catch((error) => {
                  message.error('Failed to delete all assignments');
                });
            }}
            okText="Yes"
            cancelText="No">
            <Button 
              danger type='primary' 
              icon={<DeleteOutlined />} >
              Delete All Assignments
            </Button>
          </Popconfirm>
          </Space>
        </Card>
      </Space>
    </Form>
  );
};