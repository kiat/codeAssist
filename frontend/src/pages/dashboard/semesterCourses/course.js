  import { useContext } from "react";
  import { useNavigate } from "react-router-dom";
  import { GlobalContext } from "../../../App";

  // Consider extracting styles for better maintainability and performance
  const courseStyle = {
      width: "230px",
      marginRight: "15px",
      marginBottom: "15px",
      cursor: "pointer",
  };

  const courseHeaderStyle = {
      backgroundColor: "#f0f2f5",
      height: "85px",
      paddingLeft: "10px",
  };

  const courseFooterStyle = {
      backgroundColor: "#1b807c",
      paddingLeft: "10px",
      lineHeight: "40px",
      color: "white",
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
                  <h3>{code}</h3>
                  <span>{name}</span>
              </div>
              <div style={courseFooterStyle}>
                  {assignments} assignments
              </div>
          </div>
      );
  }
