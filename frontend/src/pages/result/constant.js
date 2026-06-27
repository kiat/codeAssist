import { CheckOutlined } from "@ant-design/icons";

//assignment history column name
export const columns = [
  {
    title: "#",
    dataIndex: "order",
  },
  {
    title: "SUBMITTED AT (CDT)",
    dataIndex: "cdt",
  },
  {
    title: "SUBMITTERS",
    dataIndex: "submitters",
  },
  {
    title: "SCORE",
    dataIndex: "score",
  },
  {
    title: "ACTIVE",
    dataIndex: "active",
    render: text => {
      if (text === "1") {
        return <CheckOutlined />;
      }
    },
  },
];

export const formattingData = [
  { points: "-0", description: "Correct", id: 1, checked: 1 },
  { points: "-1", description: "Missing header comment", id: 2, checked: 0 },
  { points: "-1", description: "Lacking code comments", id: 3, checked: 1 },
  {
    points: "-1",
    description: "Inconsistent spacing/not enough spacing",
    id: 4,
    checked: 0,
  },
  { points: "-5", description: "Incomplete", id: 5, checked: 1 },
];
