import { CloseOutlined } from "@ant-design/icons";
import { Button, Col, Empty, Modal, Row, Space, Spin, Statistic } from "antd";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { scorePercent } from "../../common/format";

const BAR_COLOR = "#1890ff";

// Ticks show only each bucket's right boundary (e.g. "90%" instead of
// "80-90%") so each tick marks the line between two bars unambiguously,
// rather than a range label centered under one bar. 0% (the left edge of
// the chart, before the first bar) is implied rather than spelled out. The
// full range is always available on hover via the default Tooltip.
//
// Reads bucket_start/bucket_end directly (numeric) rather than parsing the
// display `label` string -- bucket_end is in raw points even in percentage
// mode (it's a point value the label's "X-Y%" text is derived from
// separately), so it's converted back to a percentage here. Working from
// the numbers also sidesteps string-parsing edge cases a hyphen-split
// would get wrong, like a negative raw-mode boundary ("-8.0") being
// mistaken for a range separator.
export const formatAxisTick = (bucket, mode, maxPoints) => {
  if (!bucket || bucket.bucket_start == null || bucket.bucket_end == null) {
    return bucket ? bucket.label : "";
  }
  if (mode === "percentage" && maxPoints) {
    return `${Math.round((bucket.bucket_end / maxPoints) * 100)}%`;
  }
  return `${bucket.bucket_end}`;
};

export const formatStatValue = (value, mode, maxPoints) => {
  if (value == null) return "-";
  const pct = mode === "percentage" ? scorePercent(value, maxPoints) : null;
  if (pct == null) return value;
  return `${pct}% (${value}/${maxPoints})`;
};

export default ({ open, onCancel, stats, loading, error }) => {
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
      ) : error ? (
        <Empty description='Failed to load statistics.' />
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
                tickFormatter={(_, index) => formatAxisTick(stats.histogram[index], stats.mode, stats.max_points)}
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
