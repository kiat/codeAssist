import { ExclamationCircleFilled } from "@ant-design/icons";
import { Typography } from "antd";

export default ({ text }) => {
  return (
    <div>
      <ExclamationCircleFilled />
      <span> Review and publish grades for </span>
      {/* <Button type='link'>{text}</Button> */}
      <Typography.Link>{text}</Typography.Link>
      <span> now that you're all done grading.</span>
      {/* <span> Review and publish grades for </span>
      <Button type='link'>Assignment-0</Button>
      <span>now that you're all done grading.</span> */}
    </div>
  );
};
