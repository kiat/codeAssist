import {
  PoweroffOutlined,
  QuestionCircleFilled,
  UserOutlined,
} from "@ant-design/icons";
import { useContext } from "react";
import { GlobalContext } from "../../App";
import { Link, useNavigate} from "react-router-dom";

export default function AccountPopoverContent() {
  const { updateUserInfo } = useContext(GlobalContext);
  const navigate = useNavigate();
  const userInfo = JSON.parse(localStorage.getItem("userInfo"));
  const userId = userInfo?.id;
  const isAdmin = userInfo?.isAdmin;
  
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
      {!isAdmin && (
        <>
          <hr />
          <div>
            <Link to={`/editAccount/${userId}`}>
              <UserOutlined />
              <span> Edit Account</span>
            </Link>
          </div>
        </>
      )}
      <hr />
      <div
        style={{
          cursor: "pointer",
        }}
        onClick={() => {
          localStorage.removeItem("userInfo");
          updateUserInfo(null);
          navigate('/');
        }}
      >
        <PoweroffOutlined />
        <span> Log Out</span>
      </div>
    </div>
  );
}
