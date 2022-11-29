import moment from "moment";

// column name
export const columns = [
  {
    title: "NAME",
    dataIndex: "name",
    soeter: (a, b) => a.name > b.name,
  },
  {
    title: "STATUS",
    dataIndex: "status",
    render: text => (text === 1 ? "Submitted" : "No Submission"),
  },
  {
    title: "GRADES",
    dataIndex: "grades",
    render: text => text || "-",
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
