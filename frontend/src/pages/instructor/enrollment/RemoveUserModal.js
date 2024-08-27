import { Button, Form, Input, Modal, Radio, Space, Select } from "antd";
import React, { useEffect, useState } from 'react'
import { deleteEnrollment, getCourseEnrollment } from '../../../services/enrollment';

const { Option } = Select;

function RemoveUserModal({ open, toggleAddModalOpen, onFinish, course_id, enrollment }) {
  // const [students, setStudents] = useState(["No Students"]);

  // useEffect(() => {
  //   async function fetchStudents() {
  //     let res = await getCourseEnrollment({ course_id: course_id });
  //     const updatedStudents = res.data.map((student_data) => student_data.id)
  //     setStudents(updatedStudents);
  //   }
  //   if (open) {
  //     // fetchStudents();

  //   }
  // }, [open]);
  

  // Clear form after submit
  return (
    <Modal
      open={open}
      title="Delete user from current course"
      footer={null}
      onCancel={toggleAddModalOpen}
    >
      <Form layout="vertical" onFinish={onFinish}>
        <Form.Item label="STUDENT" name="student" rules={[{ required: true, message: 'Please select a student' }]}>
          <Select>
            {enrollment.map((student, index) => (
              <Option key={index} value={student.id}>{student.sis_user_id}</Option>
            ))}
            {/* {Array.from(students).map((name, index) => (
              <Option key={index} value={name}>{name}</Option>
            ))} */}
          </Select>
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">
              Submit
            </Button>
            <Button type="primary" danger onClick={toggleAddModalOpen}>
              Cancel
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default RemoveUserModal