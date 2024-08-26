import { Button, Form, Input, Modal, Radio, Space, Select } from "antd";
import React, { useEffect, useState } from 'react'
import { getCourseEnrollment } from '../../../services/enrollment';

const { Option } = Select;

function AddTAModal({ open, toggleAddModalOpen, onFinish, course_id }) {
  const [students, setStudents] = useState(["No Students"])

  useEffect(() => {
    async function fetchStudents() {
      let res = await getCourseEnrollment({ course_id: course_id });
      console.log(res.data);
      const updatedStudents = res.data.map((student_data) => student_data.id)
      setStudents(updatedStudents);
      // Change students into the state
    }
    if (open) {
  
      // Execute your function here whenever the modal is opened
      console.log("Modal has been opened opened!");

      // query get all users from a course and save that within a state
      console.log(course_id);
      fetchStudents();

      // Upon loading the webpage, fetch the list of students
      // Then put students inside a radio option - Ig it should be eid since that's a unique identifier instead of UUID right? - yeah
      // for now do UUID and hten replace with eid

    }
  }, [open]);

  return (
    <Modal
      open={open}
      title="Add a TA to current course"
      footer={null}
      onCancel={toggleAddModalOpen}
    >
      <Form layout="vertical" onFinish={onFinish}>
        {/* <Form.Item label="EMAIL" name="email">
          <Input />
        </Form.Item>
        <Form.Item label="EID" name="eid">
          <Input />
        </Form.Item> */}
        <Form.Item label="STUDENT" name="student" required="true">
          <Select>
            {students.map((name, index) => (
              <Option key={index} value={name}>{name}</Option>
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