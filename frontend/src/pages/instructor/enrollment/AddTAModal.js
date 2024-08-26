import { Button, Form, Input, Modal, Radio, Space, Select } from "antd";
import React, { useEffect, useState } from 'react'
import { getCourseEnrollment } from '../../../services/enrollment';

const { Option } = Select;

function AddTAModal({ open, toggleAddModalOpen, onFinish, course_id, enrollment }) {
  // const [students, setStudents] = useState(["No Students"]);

  // useEffect(() => {
  //   async function fetchStudents() {
  //     let res = await getCourseEnrollment({ course_id: course_id });
  //     const updatedStudents = res.data.map((student_data) => student_data.id)
  //     setStudents(updatedStudents);
  //   }
  //   if (open) {
  //     fetchStudents();
  //   }
  // }, [open]);

  return (
    <Modal
      open={open}
      title="Add a TA to current course"
      footer={null}
      onCancel={toggleAddModalOpen}
    >
      <Form layout="vertical" onFinish={onFinish}>
        {/* <Form.Item label="STUDENT" name="student" rules={[{ required: true, message: 'Please select a student' }]}>
          <Select>
            {students.map((name, index) => (
              <Option key={index} value={name}>{name}</Option>
            ))}
          </Select>
        </Form.Item> */}
        <Form.Item label="STUDENT" name="student" rules={[{ required: true, message: 'Please select a student' }]}>
          <Select>
            {enrollment.filter(student => !student.ta).map((student, index) => (
              <Option key={index} value={student.id}>{student.sis_user_id}</Option>
            ))}
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

export default AddTAModal