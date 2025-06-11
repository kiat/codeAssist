import { useEffect, useState, useContext, useCallback } from "react";
import { Button, Form, Input, Modal, Select, Space, Typography, message } from "antd";
import axios from "axios";
import { GlobalContext } from "../../../App";
import { getCourseAssignments } from "../../../services/course";
import { duplicateAssignment } from "../../../services/assignment";

export default function DuplicateAssignmentModal({ open, toggleCreateAssignmentModal }) {
  const [courses, setCourses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState(null);
  const { courseInfo } = useContext(GlobalContext);
  
  const getCourses = useCallback(async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/courses?instructor_id=${courseInfo.instructor_id}`
      );
      setCourses(response.data);
      if (response.data.length > 0) {
        setSelectedCourseId(prevCourseId => prevCourseId || response.data[0].id);
      }
    } catch (err) {
      console.error("Error fetching courses: ", err);
      message.error("Error fetching courses");
    }
  }, [courseInfo.instructor_id]);

  const getAssignments = useCallback(async () => {
    if (!selectedCourseId) return;

    try {
      const response = await getCourseAssignments({ course_id: selectedCourseId });
      setAssignments(response.data);
    } catch (err) {
      console.error("Error fetching assignments: ", err);
      message.error("Error fetching assignments");
    }
  }, [selectedCourseId]);

  useEffect(() => {
    if (open) {
      getCourses();
    }
  }, [open, getCourses]);

  useEffect(() => {
    getAssignments();
  }, [selectedCourseId, getAssignments]);

  const courseOptions = courses.map(course => ({
    label: course.name,
    value: course.id,
  }));

  const assignmentOptions = assignments.map(assignment => ({
    label: assignment.name,
    value: assignment.id,
  }));

  const onFinish = async (values) => {
  try {
    const params = {
      oldAssignmentId: values.oldAssignment,
      newAssignmentTitle: values.newAssignment,
      currentCourseId: courseInfo.id,
    };

    const response = await duplicateAssignment(params);

    // Show a success message
    message.success("Assignment duplicated successfully");
    
    // Refresh the assignment list
    getAssignments();
    toggleCreateAssignmentModal();
    window.location.reload();

  } catch (error) {
    console.error("Error duplicating assignment:", error);
    if (error.response && error.response.data) {
      // If backend returned an error message in JSON, show it
      message.error(error.response.data.message || "Failed to duplicate assignment.");
    } else {
      // Fallback error
      message.error("An unexpected error occurred while duplicating the assignment.");
    }
  }
};

  return (
    <Modal
      title="Duplicate an Assignment"
      open={open}
      onCancel={toggleCreateAssignmentModal}
      footer={null}
    >
      <Form layout="vertical" onFinish={onFinish}>
        <Form.Item label="Select Course">
          <Select
            style={{ width: "100%" }}
            options={courseOptions}
            value={selectedCourseId}
            onChange={value => setSelectedCourseId(value)}
          />
        </Form.Item>

        <Form.Item name="oldAssignment" label="Select Assignment to Duplicate">
          <Select
            style={{ width: "100%" }}
            options={assignmentOptions}
            disabled={!selectedCourseId}
          />
        </Form.Item>

        <Form.Item
          label="COPIED ASSIGNMENT TITLE"
          name="newAssignment"
          rules={[{ required: true, message: "Please enter a title for the duplicated assignment" }]}
        >
          <Input placeholder="e.g. Homework 1" />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">
              Duplicate
            </Button>
            <Button type="primary" danger onClick={toggleCreateAssignmentModal}>
              Cancel
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
}
