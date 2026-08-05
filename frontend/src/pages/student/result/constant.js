import { CheckOutlined } from "@ant-design/icons";

// assignment history column name
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
