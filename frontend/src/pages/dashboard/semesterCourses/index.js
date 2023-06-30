import { useContext } from "react";
import { GlobalContext } from "../../../App";
import Course from "./course";
import { ConsoleSqlOutlined } from "@ant-design/icons";

/**
 * semester course modal
 * @param {*} param0
 * @returns
 */
export default function SemesterCourses({
  semesterInfo,
  toggleRelationModalOpen,
  //isFirst,
  yearInfo,
  courseGroup,
  numCourses
}) {
  const { userInfo } = useContext(GlobalContext);
  // const { semester, courses } = semesterInfo;
  // const matches = /(\d{4})(\d)/.exec(yearInfo);
  const matches = yearInfo ? yearInfo : null;
  let year,
    semester = undefined;
  if (typeof(matches) === "string") {
    if (matches.length > 5) {
      year = matches.substring(0, 4);
      semester = matches.substring(4);
    }
  }
  // if (matches) {
  //   year = matches[1];
  //   // let semester = undefined;
  //   switch (matches[2]) {
  //     case "1":
  //       semester = "Spring";
  //       break;
  //     case "2":
  //       semester = "Summer";
  //       break;
  //     case "3":
  //       semester = "Fall";
  //       break;
  //     case "4":
  //       semester = "Winetr";
  //       break;
  //     default:
  //       break;
  //   }
  // }
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
        {(numCourses === 0) || (numCourses > 0 && courseGroup === 1) ? (
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
