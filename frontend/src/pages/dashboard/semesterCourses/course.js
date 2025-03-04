  import { useContext } from "react";
  import { useNavigate } from "react-router-dom";
  import { GlobalContext } from "../../../App";

const courseStyle = {
    width: "230px",
    height: "140px",
    cursor: "pointer",
    overflow: "hidden", 
    boxShadow: "0px 2px 5px rgba(0, 0, 0, 0.1)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    backgroundColor: "#F5F5F5",
};

const courseHeaderStyle = {
    backgroundColor: "#f0f2f5",
    height: "85px",
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
    padding: "10px",
    fontWeight: "bold",
    fontSize: "16px",
    color: "#333",
};

const courseFooterStyle = {
    backgroundColor: "#1b807c",
    color: "white",
    textAlign: "center",
    padding: "12px", 
    fontSize: "14px",
    fontWeight: "bold", 
};

  /**
   * Displays a single course with navigation based on user role
   * @param {Object} courseInfo Information about the course
   */
  export default function Course({ courseInfo }) {
      const navigate = useNavigate();
      const { userInfo, updateCourseInfo } = useContext(GlobalContext);
      const { code, name, assignments, id, semester } = courseInfo;

      function handleCourseClick() {
          // Ensure all fields are updated correctly in context
          updateCourseInfo({
              id: id,
              code: code,
              name: name,
              semester: semester,
              year: courseInfo.year || ""  // Handle missing year if not provided
          });

          // Navigate based on user role
          const destination = userInfo.isStudent ? `/assignments/${id}` : `/instructorDashboard/${id}`;
          navigate(destination);
      }

    return (
        <div style={courseStyle} onClick={handleCourseClick}>
            <div style={courseHeaderStyle}>
                <span>{name}</span>
            </div>
            <div style={courseFooterStyle}>
                {assignments} Assignments
            </div>
        </div>
    );
}
