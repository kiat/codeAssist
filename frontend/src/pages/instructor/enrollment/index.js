import {
  Button,
  Card,
  Checkbox,
  Dropdown,
  Input,
  PageHeader,
  Select,
  Space,
  Table,
  Typography,
  message
} from "antd";
import { PlusOutlined, DownOutlined } from "@ant-design/icons";
import AddUserModal from "./AddUserModal";
import { useCallback, useState, useContext } from "react";
import {
  createEnrollment,
  createEnrollmentCSV,
  getCourseEnrollment,
  updateRole
} from "../../../services/course";
import {
  getUserByEmail,
} from "../../../services/user";
import { useParams } from "react-router-dom";
import { useEffect } from "react";
import AddMoreUsersModal from "./AddMoreUsersModal";
import { GlobalContext } from "../../../App";
import AddCSVModal from "./AddCSVModal";
import RolePill from "../../../components/RolePill";
const ROLE_ORDER = { instructor: 0, ta: 1, student: 2 };

function roleSort(a, b) {
  const ra = ROLE_ORDER[a.role?.toLowerCase()] ?? 3;
  const rb = ROLE_ORDER[b.role?.toLowerCase()] ?? 3;
  if (ra !== rb) return ra - rb;
  return (a.name || "").localeCompare(b.name || "");
}

const columns = [
  { title: "NAME", dataIndex: "name", sorter: (a, b) => (a.name || "").localeCompare(b.name || "") },
  { title: "EMAIL", dataIndex: "email_address" },
];

export default () => {
  const { userInfo, courseRole } = useContext(GlobalContext);
  const isTA = courseRole === "ta";

  const [filterRoles, setFilterRoles] = useState([]);
  const [filterName, setFilterName] = useState("");
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [addCSVModalOpen, setAddCSVModalOpen] = useState(false);
  const [addMoreUsersModalOpen, setAddMoreUsersModalOpen] = useState(false);
  const [originalEnrollment, setOriginalEnrollment] = useState([]);
  const [enrollment, setEnrollment] = useState([]);

  const { courseId } = useParams();

  const toggleAddModalOpen = useCallback(() => {
    setAddModalOpen((t) => !t);
  }, []);
  
  const toggleAddCSVModalOpen = useCallback(() => {
    setAddCSVModalOpen((t) => !t);
  }, []);

  const toggleAddMoreUsersModalOpen = useCallback(() => {
    setAddMoreUsersModalOpen((t) => !t);
  }, []);

  const getEnrollment = useCallback(() => {
    getCourseEnrollment({ course_id: courseId }).then((res) => {
      setEnrollment(res.data);
      setOriginalEnrollment(res.data); 
    });
  }, [courseId]);


  const handleUpdateRole = useCallback(
    async (newRole, studentId) => {
      try {
        await updateRole({
          "student_id": studentId,
          "course_id": courseId,
          "new_role": newRole,
        });
        message.info("User role updated")
        getEnrollment();
      }
      catch(error) {
        console.error("Error updating role: ", error);
      }
    },
    [courseId, getEnrollment]
  );

  const finishForm =  useCallback(
    async (values) => {
      const { email } = values;

      try {
        const res = await getUserByEmail({ email: email });
        await createEnrollment({
          student_id: res.data.id,
          course_id: courseId,
          role: values.role,
        });
        message.success("Successfully created enrollment")
        toggleAddModalOpen();
        getEnrollment();
      }
      catch(error) {
        console.error("Error creating enrollments: ", error);
      }
    }, [courseId, getEnrollment, toggleAddModalOpen]
  );
  
  const finishCSVForm = useCallback(
    async (formData) => {
      formData.append("course_id", courseId);

      return createEnrollmentCSV(formData)
        .then((res) => res.data)
  }, [courseId]);
  
  const finishMoreUsers = useCallback(
    (values) => {
      console.log(values);
      values.forEach(enrollEntry);

      async function enrollEntry(item) {
        try {
          const res = await getUserByEmail({ email: item });
          await createEnrollment({
            student_id: res.data.id,
            course_id: courseId,
            role: values.role,
          });
          message.success("Successfully created enrollment")
          getEnrollment();
        }
        catch(error) {
          console.error("Error creating enrollments: ", error);
        }
      }
      toggleAddMoreUsersModalOpen();
    },
    [courseId, getEnrollment, toggleAddMoreUsersModalOpen]
  );

  useEffect(() => {
    getEnrollment();
  }, [getEnrollment, courseId]);

  useEffect(() => {
    let filtered = originalEnrollment;
    if (filterRoles.length > 0) {
      filtered = filtered.filter((e) => filterRoles.includes(e.role?.toLowerCase()));
    }
    if (filterName.trim()) {
      filtered = filtered.filter((e) =>
        e.name.toLowerCase().includes(filterName.toLowerCase())
      );
    }
    setEnrollment(filtered);
  }, [originalEnrollment, filterRoles, filterName]);
  // count the number of students, instructors, and TAs for the course
  const studentCount = originalEnrollment.filter(
    (e) => e.role?.toLowerCase() === "student"
  ).length;
  const instructorCount = originalEnrollment.filter(
    (e) => e.role?.toLowerCase() === "instructor"
  ).length;
  const taCount = originalEnrollment.filter(
    (e) => e.role?.toLowerCase() === "ta"
  ).length;
  return (
    <>
      <PageHeader
        title="Course Roster"
        style={{ borderBottom: "1px solid #f0f0f0" }}
      />
      <Card bordered={false}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20, flexWrap: "wrap" }}>
          <Checkbox.Group
            value={filterRoles}
            onChange={setFilterRoles}
            options={[
              { label: "Student", value: "student" },
              { label: "TA", value: "ta" },
              { label: "Instructor", value: "instructor" },
            ]}
          />
          <Input
            placeholder="search by name"
            value={filterName}
            onChange={(e) => setFilterName(e.target.value)}
            allowClear
            style={{ width: 200 }}
          />
          <Button
            onClick={() => { setFilterRoles([]); setFilterName(""); }}
            disabled={filterRoles.length === 0 && !filterName}
          >
            Reset
          </Button>
        </div>
        <Table
          columns={[
            ...columns,
            {
              title: "ROLE",
              dataIndex: "role",
              sorter: (a, b) => roleSort(a, b),
              render: (text, record) => {
                const normalised = text?.toLowerCase();
                if (isTA || normalised === "instructor") {
                  return <RolePill role={normalised} />;
                }
                const items = [
                  { key: "student", label: <RolePill role="student" /> },
                  { key: "ta",      label: <RolePill role="ta" /> },
                ];
                return (
                  <Dropdown
                    menu={{ items, onClick: ({ key }) => handleUpdateRole(key, record.id) }}
                    trigger={["click"]}
                  >
                    <span style={{ cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 4 }}>
                      <RolePill role={normalised} />
                      <DownOutlined style={{ fontSize: 10, color: "#9ca3af" }} />
                    </span>
                  </Dropdown>
                );
              },
            },
          ]}
          dataSource={[...enrollment].sort(roleSort)}
          rowKey="id"
        />
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
        <Space size="large">
          <Typography.Title level={5}> {studentCount} students</Typography.Title>
          <Typography.Title level={5}> {instructorCount} instructors</Typography.Title>
          <Typography.Title level={5}> {taCount} TAs</Typography.Title>
        </Space>
        <div
          style={{
            float: "right",
            marginRight: "225px",
          }}
        >
          <Space>
            {/* <Button icon={<UploadOutlined />}>Download Enrollment</Button> */}
            <Button icon={<PlusOutlined />} onClick={toggleAddModalOpen}>
              Add Students or Staff
            </Button>
            <Button icon={<PlusOutlined />} onClick={toggleAddCSVModalOpen}>
              Add With CSV
            </Button>
            <Button
              icon={<PlusOutlined />}
              onClick={toggleAddMoreUsersModalOpen}
            >
              Add More Students
            </Button>
          </Space>
        </div>
      </div>
      <AddUserModal
        open={addModalOpen}
        toggleAddModalOpen={toggleAddModalOpen}
        onFinish={finishForm}
        isTA={isTA}
      />
      <AddCSVModal 
        open={addCSVModalOpen} 
        toggleAddCSVModalOpen={toggleAddCSVModalOpen} 
        finishCSVForm={finishCSVForm} 
        getEnrollment={getEnrollment}
      />
      <AddMoreUsersModal
        toggleAddMoreUsersModalOpen={toggleAddMoreUsersModalOpen}
        open={addMoreUsersModalOpen}
        finishMoreUsers={finishMoreUsers}
      />
    </>
  );
};
