import { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { GlobalContext } from "../../../App";

/**
 * course modals
 * @param {*} param0
 * @returns
 */
export default function Course({ courseInfo }) {
  const navigate = useNavigate();
  const { code, name, assignmentCount, id } = courseInfo;
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
        // click on the course and jump to the assignment page
        if (userInfo.isStudent) {
          navigate(`/assignments/${id}`);
        } else {
          navigate("/instructorDashboard");
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
        {assignmentCount} assignments
      </div>
    </div>
  );
}
