import { useEffect, useState, useContext, useCallback } from "react";
import { Button, Form, Input, Modal, Select, Space, Typography, message } from "antd";
import axios from "axios";
import { GlobalContext } from "../../../App";
import { getCourseAssignments } from "../../../services/course";

export default function DuplicateAssignmentModal({ open, toggleCreateAssignmentModal }) {
  const [courses, setCourses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState(null);
  const { courseInfo } = useContext(GlobalContext);
  
  /** Fetch courses for the instructor */
  const getCourses = useCallback(async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/courses?instructor_id=${courseInfo.instructor_id}`
      );
      setCourses(response.data);

      // Automatically select a default course
      if (response.data.length > 0) {
        setSelectedCourseId(prevCourseId => prevCourseId || response.data[0].id);
      }
    } catch (err) {
      console.error("Error fetching courses: ", err);
      message.error("Error fetching courses");
    }
  }, [courseInfo.instructor_id]);

  /** Fetch assignments for the selected course */
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

  /** When modal opens, load courses */
  useEffect(() => {
    if (open) {
      getCourses();
    }
  }, [open, getCourses]);

  /** When selected course changes, load assignments */
  useEffect(() => {
    getAssignments();
  }, [selectedCourseId, getAssignments]);

  /** Map courses & assignments to dropdown options */
  const courseOptions = courses.map(course => ({
    label: course.name,
    value: course.id,
  }));

  const assignmentOptions = assignments.map(assignment => ({
    label: assignment.name,
    value: assignment.id,
  }));

  /** Handle form submission */
  const onFinish = async (values) => {
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/duplicate_assignment`,
        {
          oldAssignmentId: values.oldAssignment,
          newAssignmentTitle: values.newAssignment,
          currentCourseId: courseInfo.id,
        }
      );
      console.log("Assignment duplicated successfully:", response.data);
      message.success("Assignment duplicated successfully");
      toggleCreateAssignmentModal();
      getAssignments(); // Refresh the assignments list for the selected course
      window.location.reload();
    } catch (error) {
      console.error("Error duplicating assignment:", error);
      message.error("There was an error duplicating the assignment");
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
        {/* Course selection dropdown */}
        <Form.Item label="Select Course">
          <Select
            style={{ width: "100%" }}
            options={courseOptions}
            value={selectedCourseId}
            onChange={value => setSelectedCourseId(value)}
          />
        </Form.Item>

        {/* Assignment selection dropdown */}
        <Form.Item name="oldAssignment" label="Select Assignment to Duplicate">
          <Select
            style={{ width: "100%" }}
            options={assignmentOptions}
            disabled={!selectedCourseId}
          />
        </Form.Item>

        <Form.Item label="COPIED ASSIGNMENT TITLE" name="newAssignment">
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
