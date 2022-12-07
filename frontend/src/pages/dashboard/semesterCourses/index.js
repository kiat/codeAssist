import { useContext } from "react";
import { GlobalContext } from "../../../App";
import Course from "./course";

/**
 * semester course modal
 * @param {*} param0
 * @returns
 */
export default function SemesterCourses({
  semesterInfo,
  toggleRelationModalOpen,
  isFirst,
  yearInfo,
}) {
  const { userInfo } = useContext(GlobalContext);
  // const { semester, courses } = semesterInfo;
  const matches = /(\d{4})(\d)/.exec(yearInfo);
  let year,
    semester = undefined;
  if (matches) {
    year = matches[1];
    // let semester = undefined;
    switch (matches[2]) {
      case "1":
        semester = "Spring";
        break;
      case "2":
        semester = "Summer";
        break;
      case "3":
        semester = "Fall";
        break;
      case "4":
        semester = "Winetr";
        break;
      default:
        break;
    }
  }
  // const semester = matches[2] === 1 ? 'Spring' : ();
  return (
    <div
      style={{
        marginBottom: "20px",
        display:
          semesterInfo.length > 0 || !userInfo?.isStudent ? "inline" : "none",
      }}
    >
      <h3>{year && semester ? `${semester} ${year}` : null}</h3>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
        }}
      >
        {semesterInfo?.map(item => (
          <Course key={item.name} courseInfo={item} />
        ))}
        {isFirst && !userInfo?.isStudent ? (
          <div
            style={{
              border: "1px dashed green",
              width: "230px",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              color: "green",
              fontSize: "bold",
              cursor: "pointer",
              height: "125px",
            }}
            onClick={toggleRelationModalOpen}
          >
            + Add a course
          </div>
        ) : null}
      </div>
    </div>
  );
}
