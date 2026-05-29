import { useState } from "react";
import { Input, Table, PageHeader, Card, Space, Button, message } from "antd";
import { useNavigate } from "react-router-dom";

export default function AdminInstructors() {
  const [instructors, setInstructors] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async () => {
    if (!search.trim()) {
      message.info("Please enter a search term.");
      return;
    }
    setLoading(true);
    setSearched(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/get_all_instructors`);
      const data = await res.json();
      setInstructors(
        data.filter(i =>
          i.name?.toLowerCase().includes(search.toLowerCase()) ||
          i.sis_user_id?.toLowerCase().includes(search.toLowerCase())
        )
      );
    } catch (e) {
      message.error("Failed to fetch instructors");
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: "Name", dataIndex: "name", key: "name" },
    { title: "EID", dataIndex: "sis_user_id", key: "eid" },
    { title: "Email", dataIndex: "email_address", key: "email" },
    {
      title: "Actions",
      key: "actions",
      render: (_, record) => (
        <Button type="primary" onClick={() => navigate(`/admin/instructors/manage/${record.id}`)}>
          Manage
        </Button>
      ),
    },
  ];

  return (
    <Card>
      <PageHeader title="Search Instructors" />
      <Space direction="vertical" style={{ width: "100%" }}>
        <Space>
          <Input.Search
            placeholder="Search by name or EID"
            value={search}
            onChange={e => setSearch(e.target.value)}
            enterButton
            style={{ width: 500 }}
            loading={loading}
            onSearch={handleSearch}
          />
          <Button type="default" onClick={() => navigate("/admin/instructors/add")}>
            Add Instructor
          </Button>
        </Space>
        <Table rowKey="id" columns={columns} dataSource={searched ? instructors : []} loading={loading} />
      </Space>
    </Card>
  );
}