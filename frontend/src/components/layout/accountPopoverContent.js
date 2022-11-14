import {
  PoweroffOutlined,
  QuestionCircleFilled,
  UserOutlined,
} from "@ant-design/icons";
import { useContext } from "react";
import { GlobalContext } from "../../App";

export default function AccountPopoverContent() {
  const { updateUserInfo } = useContext(GlobalContext);
  return (
    <div
      style={{
        width: "160px",
      }}
    >
      <div>
        <QuestionCircleFilled />
        <span> Help</span>
      </div>
      <hr />
      <div>
        <UserOutlined />
        <span> Edit Account</span>
      </div>
      <hr />
      <div
        style={{
          cursor: "pointer",
        }}
        onClick={() => {
          localStorage.removeItem("userInfo");
          updateUserInfo(null);
        }}
      >
        <PoweroffOutlined />
        <span> Log Out</span>
      </div>
    </div>
  );
}
