import { useEffect, useState } from "react";
import { CloseOutlined } from "@ant-design/icons";
import { Button, Col, Empty, Modal, Row, Space, Spin, Statistic, message } from "antd";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getGradeStatistics } from "../../services/submission";

const BAR_COLOR = "#1890ff";

// Ticks show only each bucket's right boundary (e.g. "90%" instead of
// "80-90%") so each tick marks the line between two bars unambiguously,
// rather than a range label centered under one bar. 0% (the left edge of
// the chart, before the first bar) is implied rather than spelled out. The
// full range is always available on hover via the default Tooltip, which
// reads the unmodified `label` field.
const formatAxisTick = (label) => {
  if (!label.includes("-")) return label;
  return label.split("-").pop();
};

const formatStatValue = (value, mode, maxPoints) => {
  if (value == null) return "-";
  if (mode === "percentage" && maxPoints) {
    const pct = Math.round((value / maxPoints) * 100);
    return `${pct}% (${value}/${maxPoints})`;
  }
  return value;
};

export default ({ open, onCancel, assignmentId }) => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (!open) return;

    setLoading(true);
    (async () => {
      try {
        const response = await getGradeStatistics({ assignment_id: assignmentId });
        setStats(response.data);
      } catch (err) {
        message.error("Failed to load statistics.");
      } finally {
        setLoading(false);
      }
    })();
  }, [open, assignmentId]);

  const hasData = stats && stats.count > 0;

  return (
    <Modal
      open={open}
      title='Statistics'
      width={820}
      closable={false}
      onCancel={onCancel}
      footer={
        <Button icon={<CloseOutlined />} onClick={onCancel}>
          Close
        </Button>
      }
    >
      {loading ? (
        <Space style={{ width: "100%", justifyContent: "center", padding: "32px 0" }}>
          <Spin />
        </Space>
      ) : !hasData ? (
        <Empty description='No graded submissions yet.' />
      ) : (
        <Space direction='vertical' style={{ width: "100%" }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic title='Mean' value={formatStatValue(stats.mean, stats.mode, stats.max_points)} />
            </Col>
            <Col span={6}>
              <Statistic title='Median' value={formatStatValue(stats.median, stats.mode, stats.max_points)} />
            </Col>
            <Col span={6}>
              <Statistic title='Min' value={formatStatValue(stats.min, stats.mode, stats.max_points)} />
            </Col>
            <Col span={6}>
              <Statistic title='Max' value={formatStatValue(stats.max, stats.mode, stats.max_points)} />
            </Col>
          </Row>
          {stats.mode === "raw" && (
            <div style={{ color: "rgba(0, 0, 0, 0.45)" }}>
              This assignment has no configured point total, so scores are shown as raw points.
            </div>
          )}
          <ResponsiveContainer width='100%' height={280}>
            <BarChart data={stats.histogram} barCategoryGap={4} barGap={0}>
              <CartesianGrid vertical={false} stroke='#f0f0f0' />
              <XAxis
                dataKey='label'
                tick={{ fontSize: 12 }}
                tickFormatter={formatAxisTick}
                interval={0}
              />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey='count' fill={BAR_COLOR} radius={[4, 4, 0, 0]} maxBarSize={24} />
            </BarChart>
          </ResponsiveContainer>
        </Space>
      )}
    </Modal>
  );
};
