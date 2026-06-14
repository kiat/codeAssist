import React, { useState, useEffect, useCallback } from "react";
import { Modal, List, Tag, Button, Spin, Empty, message } from "antd";
import { HistoryOutlined, FileOutlined, ClockCircleOutlined } from "@ant-design/icons";
import moment from "moment";

/**
 * VersionHistoryModal — shows a list of auto-saved and manual draft versions.
 *
 * Props:
 *   open             – boolean
 *   onCancel         – () => void
 *   onSelectVersion  – (content) => void
 *   studentId        – string
 *   assignmentId     – string
 */
export default function VersionHistoryModal({
  open,
  onCancel,
  onSelectVersion,
  studentId,
  assignmentId,
}) {
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchDrafts = useCallback(async () => {
    if (!studentId || !assignmentId) return;
    setLoading(true);
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/get_code_drafts?student_id=${studentId}&assignment_id=${assignmentId}`
      );
      const data = await response.json();
      setDrafts(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to fetch drafts:", error);
      message.error("Failed to load version history");
    } finally {
      setLoading(false);
    }
  }, [studentId, assignmentId]);

  useEffect(() => {
    if (open) {
      fetchDrafts();
    }
  }, [open, fetchDrafts]);

  const handleSelect = (draft) => {
    onSelectVersion(draft.content);
    onCancel();
  };

  return (
    <Modal
      title={
        <span>
          <HistoryOutlined style={{ marginRight: 8 }} />
          Version History
        </span>
      }
      open={open}
      onCancel={onCancel}
      footer={null}
      width={600}
    >
      {loading ? (
        <div style={{ textAlign: "center", padding: 40 }}>
          <Spin />
        </div>
      ) : drafts.length === 0 ? (
        <Empty description="No saved versions yet" />
      ) : (
        <List
          dataSource={drafts}
          renderItem={(draft) => (
            <List.Item
              style={{ cursor: "pointer", padding: "10px 12px" }}
              onClick={() => handleSelect(draft)}
              actions={[
                <Button type="link" size="small">
                  Restore
                </Button>,
              ]}
            >
              <List.Item.Meta
                avatar={
                  <div
                    style={{
                      width: 36,
                      height: 36,
                      borderRadius: 6,
                      backgroundColor: draft.auto_saved ? "#e6f7ff" : "#f6ffed",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <FileOutlined
                      style={{
                        fontSize: 16,
                        color: draft.auto_saved ? "#1890ff" : "#52c41a",
                      }}
                    />
                  </div>
                }
                title={
                  <span>
                    Version {draft.version_number}
                    {draft.auto_saved ? (
                      <Tag color="blue" style={{ marginLeft: 8, fontSize: 11 }}>
                        Auto-saved
                      </Tag>
                    ) : (
                      <Tag color="green" style={{ marginLeft: 8, fontSize: 11 }}>
                        Manual save
                      </Tag>
                    )}
                  </span>
                }
                description={
                  <span style={{ fontSize: 12, color: "#999" }}>
                    <ClockCircleOutlined style={{ marginRight: 4 }} />
                    {moment(draft.saved_at).format("MMM D, YYYY [at] h:mm:ss A")}
                    <span style={{ marginLeft: 12 }}>
                      {draft.content ? draft.content.split("\n").length : 0} lines
                    </span>
                  </span>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Modal>
  );
}
