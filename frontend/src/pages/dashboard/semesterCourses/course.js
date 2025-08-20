import { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { GlobalContext } from "../../../App";

const courseStyle = {
    width: "230px",
    minHeight: "138px", 
    cursor: "pointer",
    overflow: "hidden",
    boxShadow: "0px 2px 5px rgba(0, 0, 0, 0.1)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    backgroundColor: "#F5F5F5",
};

const courseHeaderContainer = {
    display: "flex",
    flexDirection: "column", 
    padding: "10px",
    borderTopLeftRadius: "3px",
    borderTopRightRadius: "3px",
};

const courseHeaderStyle = {
    fontWeight: "bold",
    fontSize: "16px",
    color: "#333",
};

const descriptionStyle = {
    fontSize: "13px",
    color: "#555",
    marginTop: "4px",
};

const courseFooterStyle = {
    backgroundColor: "#1b807c",
    color: "white",
    textAlign: "left",
    padding: "10px",
    fontSize: "14px",
    fontWeight: "bold",
    borderBottomLeftRadius: "3px",
    borderBottomRightRadius: "3px",
};

export default function Course({ courseInfo }) {
    const navigate = useNavigate();
    const { userInfo, updateCourseInfo } = useContext(GlobalContext);
    const { name, assignments, description, id, semester } = courseInfo;

    function handleCourseClick() {
        updateCourseInfo({
            id,
            name,
            semester,
            year: courseInfo.year || "",
        });

        const destination = userInfo.isStudent ? `/assignments/${id}` : `/instructorDashboard/${id}`;
        navigate(destination);
    }

    return (
        <div style={courseStyle} onClick={handleCourseClick}>
            <div style={courseHeaderContainer}>
                <div style={courseHeaderStyle}>{name}</div>
                <div style={descriptionStyle}>
                    {description}
                </div>
            </div>
            <div style={courseFooterStyle}>
                {assignments} Assignments
            </div>
        </div>
    );
}