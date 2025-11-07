import { Modal, Table } from "antd";
import axios from "axios";
import { useEffect, useState } from "react";
import { columns } from "./constant";

/**
 * assignment submission history window modal
 * @param {*} param0
 * @returns
 */
export default function SubmissionHistoryModal({ open, onCancel }) {
  const [tableData, setTableData] = useState([]);

  const getSubmissionHistory = () => {
    axios.post("/api/submissionHistory").then(res => {
      setTableData(res.data.history);
    });
  };

  useEffect(() => {
    getSubmissionHistory();
  }, []);

  return (
    <Modal
      title='Submission history'
      open={open}
      onCancel={onCancel}
      footer={null}
      width={600}
    >
      <Table columns={columns} dataSource={tableData} rowKey='id' />
    </Modal>
  );
}
