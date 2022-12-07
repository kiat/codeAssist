import {
  Button,
  Card,
  Form,
  Input,
  PageHeader,
  Select,
  Space,
  Table,
  Typography,
} from "antd";
import { PlusOutlined, UploadOutlined } from "@ant-design/icons";
import AddUserModal from "./AddUserModal";
import { useCallback, useState } from "react";
import {
  createEnrollment,
  getCourseEnrollment,
} from "../../../services/enrollment";
import { useParams } from "react-router-dom";
import { useEffect } from "react";

const columns = [
  { title: "FIRST & LAST NAME", dataIndex: "name" },
  { title: "EMAIL", dataIndex: "email" },
  // { title: "ROLE", dataIndex: "role" },
  // { title: "SECTIONS", dataIndex: "sections" },
  // { title: "SUBMISSIONS", dataIndex: "submissions" },
  // {
  //   title: "REMOVE",
  //   render: () => (
  //     <Button type='primary' size='small' danger icon={<CloseOutlined />} />
  //   ),
  // },
];

export default () => {
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [enrollment, setEnrollment] = useState([]);
  const { courseId } = useParams();

  const toggleAddModalOpen = useCallback(() => {
    setAddModalOpen(t => !t);
  }, []);

  const getEnrollment = useCallback(() => {
    getCourseEnrollment({ course_id: courseId }).then(res => {
      setEnrollment(res.data);
    });
  }, [courseId]);

  const finishForm = useCallback(
    values => {
      const { studentId } = values;
      createEnrollment({ student_id: studentId, course_id: courseId }).then(
        res => {
          toggleAddModalOpen();
          getEnrollment();
        }
      );
    },
    [courseId, getEnrollment, toggleAddModalOpen]
  );

  useEffect(() => {
    getEnrollment();
  }, [getEnrollment]);

  return (
    <>
      <PageHeader
        title='Course Roster'
        style={{ borderBottom: "1px solid #f0f0f0" }}
      />
      <Card bordered={false}>
        <Form layout='inline' style={{ marginBottom: "20px" }}>
          <Form.Item name='role'>
            <Select
              placeholder='view by role'
              style={{ width: "180px" }}
              options={[
                { label: "All", value: "0" },
                { label: "Students", value: "1" },
                { label: "Instructors", value: "2" },
                { label: "TAs", value: "3" },
                { label: "Readers", value: "4" },
              ]}
            />
          </Form.Item>
          <Form.Item name='section'>
            <Input placeholder='view by section' />
          </Form.Item>
          <Form.Item name='username'>
            <Input placeholder='view by name' />
          </Form.Item>
          <Form.Item>
            <Button type='primary'>search</Button>
          </Form.Item>
        </Form>
        <Table columns={columns} dataSource={enrollment} rowKey='id' />
      </Card>
      <div
        style={{
          backgroundColor: "#1890ff",
          position: "fixed",
          width: "100%",
          bottom: 0,
          lineHeight: "40px",
          color: "white",
          fontWeight: "bold",
          marginLeft: "-1px",
        }}
      >
        <Space size='large'>
          <Typography.Title level={5}>50 students</Typography.Title>
          <Typography.Title level={5}>2 instructors</Typography.Title>
          <Typography.Title level={5}>2 TAs</Typography.Title>
        </Space>
        <div
          style={{
            float: "right",
            marginRight: "225px",
          }}
        >
          <Space>
            <Button icon={<UploadOutlined />}>Download Enrollment</Button>
            <Button icon={<PlusOutlined />} onClick={toggleAddModalOpen}>
              Add Students or Staff
            </Button>
          </Space>
        </div>
      </div>
      <AddUserModal
        open={addModalOpen}
        toggleAddModalOpen={toggleAddModalOpen}
        onFinish={finishForm}
      />
    </>
  );
};
