import moment from "moment";

// column names of assignment
export const columns = [
  {
    title: "NAME",
    dataIndex: "name",
  },
  {
    title: "STATUS",
    dataIndex: "status",
    render: text => (text === 1 ? "Submitted" : "No Submission"),
  },
  {
    title: "RELEASED",
    dataIndex: "released",
    render: text => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
  },
  {
    title: "DUE(CDT)",
    dataIndex: "due",
    render: text => moment(text).format("MMM DD [AT] h:mmA").toUpperCase(),
  },
];
