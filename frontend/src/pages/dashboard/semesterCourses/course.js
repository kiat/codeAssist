import { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { GlobalContext } from "../../../App";

/**
 * course modal
 * @param {*} param0
 * @returns
 */
export default function Course({ courseInfo }) {
  const navigate = useNavigate();
  const { code, name, assignments, id } = courseInfo;
  const { userInfo, updateCourseInfo } = useContext(GlobalContext);

  return (
    <div
      style={{
        width: "230px",
        marginRight: "15px",
        marginBottom: "15px",
        cursor: "pointer",
      }}
      onClick={() => {
        updateCourseInfo({
          id: id,
          code: code,
          name: name,
          // semester: semester,
        });
        //click assignments and navigate to destination assignment page
        if (userInfo.isStudent) {
          navigate(`/assignments/${id}`);
        } else {
          navigate(`/instructorDashboard/${id}`);
        }
      }}
    >
      <div
        style={{
          backgroundColor: "#f0f2f5",
          height: "85px",
          paddingLeft: "10px",
        }}
      >
        <h3>{code}</h3>
        <span>{name}</span>
      </div>
      <div
        style={{
          backgroundColor: "#1b807c",
          paddingLeft: "10px",
          lineHeight: "40px",
          color: "white",
        }}
      >
        {assignments} assignments
      </div>
    </div>
  );
}
