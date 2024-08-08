import { useEffect, useState, useContext, useCallback } from "react";
import { Button, Form, Input, Modal, Select, Space, Typography, message } from "antd";
import axios from "axios";
import { GlobalContext } from "../../../App";
import { useNavigate, useParams } from "react-router-dom";
import { getCourseAssignments } from "../../../services/course";

export default function DuplicateAssignmentModal({ open, toggleCreateAssignmentModal }) {
  const [assignments, setAssignments] = useState([]);
  const { courseInfo } = useContext(GlobalContext);
  const { courseId } = useParams();
  const navigate = useNavigate();

  const getAssignments = useCallback(() => {
    getCourseAssignments({ course_id: courseId }).then(res => {
      setAssignments(res.data);
    });
  }, [courseId]);

  useEffect(() => {
    if (open) {
      getAssignments();
    }
  }, [open, getAssignments]);

  const assignmentOptions = assignments.map(assignment => ({
    label: assignment.name,
    value: assignment.id
  }));

  const onFinish = (values) => {
    axios.post(`${process.env.REACT_APP_API_URL}/duplicate_assignment`, {
      oldAssignmentId: values.oldAssignment,
      newAssignmentTitle: values.newAssignment,
    })
    .then(response => {
      console.log("Assignment duplicated successfully:", response.data);
      message.success("Assignment duplicated successfully");
      toggleCreateAssignmentModal();
      getAssignments(); // Refresh the assignments list
      window.location.reload(); // Force a page reload to show the updated assignments list
    })
    .catch(error => {
      console.error("There was an error duplicating the assignment!", error);
      message.error("There was an error duplicating the assignment");
    });
  };

  return (
    <Modal
      title='Duplicate an Assignment'
      open={open}
      onCancel={toggleCreateAssignmentModal}
      footer={null}
    >
      <Form layout='vertical' onFinish={onFinish}>
        <Form.Item
          name='oldAssignment'
          label={
            <div>
              <Typography.Title level={4} style={{ marginBottom: 0 }}>
                {courseInfo.name}
              </Typography.Title>
              <Typography.Title level={5} style={{ marginTop: 0 }}>
                {courseInfo.semester} {courseInfo.year}
              </Typography.Title>
            </div>
          }
        >
          <Select
            style={{ width: "100%" }}
            options={assignmentOptions}
          />
        </Form.Item>
        <Form.Item label='COPIED ASSIGNMENT TITLE' name='newAssignment'>
          <Input placeholder='e.g. Homework 1' />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type='primary' htmlType='submit'>
              Duplicate
            </Button>
            <Button type='primary' danger onClick={toggleCreateAssignmentModal}>
              Cancel
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
}
